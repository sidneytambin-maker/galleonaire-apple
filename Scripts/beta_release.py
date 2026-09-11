"""Prepare and submit only the verified Galleonaire build for TestFlight review."""
import argparse
import json
import urllib.parse
from pathlib import Path

from beta_metadata import ROOT, native_gate, resolve_app


def query(resource, **filters):
    return resource + "?" + urllib.parse.urlencode({"filter[" + k + "]": v for k, v in filters.items()})


def checked_build(apple, number, version):
    app_id = resolve_app(apple)
    builds = apple.request("GET", query("builds", app=app_id, version=str(number)))["data"]
    if len(builds) != 1:
        raise ValueError("The exact release build has not appeared in Apple processing yet")
    build = builds[0]
    attributes = build["attributes"]
    if attributes.get("version") != str(number) or attributes.get("processingState") != "VALID" or attributes.get("expired") is not False:
        raise ValueError("The release build is not valid and unexpired")
    base = "builds/" + build["id"]
    owner = apple.request("GET", base + "/app")["data"]
    release = apple.request("GET", base + "/preReleaseVersion")["data"]
    if owner["id"] != app_id or release["attributes"].get("version") != version or release["attributes"].get("platform") != "IOS":
        raise ValueError("The build belongs to a different app, version or platform")
    if attributes.get("usesNonExemptEncryption") is not False:
        raise ValueError("Apple has not confirmed the build's export compliance declaration")
    return app_id, build["id"]


def checked_groups(apple, app_id, metadata):
    groups = apple.request("GET", query("betaGroups", app=app_id))["data"]
    result = []
    for name, internal in [(metadata["internalGroup"], True), (metadata["externalGroup"], False)]:
        matches = [group for group in groups if group["attributes"]["name"] == name]
        if len(matches) != 1 or matches[0]["attributes"].get("isInternalGroup") is not internal:
            raise ValueError("Configure the expected internal and external beta groups first")
        owner = apple.request("GET", "betaGroups/" + matches[0]["id"] + "/app")["data"]
        if owner["id"] != app_id:
            raise ValueError("Refusing to change another app's beta group")
        result.append(matches[0]["id"])
    return result


def prepare(apple, number, metadata):
    app_id, build_id = checked_build(apple, number, metadata["version"])
    groups = checked_groups(apple, app_id, metadata)
    notes = metadata.get("whatToTest", "")
    if not isinstance(notes, str) or not 20 <= len(notes) <= 4000:
        raise ValueError("The build needs meaningful testing notes")
    base = "builds/" + build_id
    localizations = apple.request("GET", base + "/betaBuildLocalizations")["data"]
    locale = next((item for item in localizations if item["attributes"]["locale"] == metadata["primaryLocale"]), None)
    if locale:
        apple.request("PATCH", "betaBuildLocalizations/" + locale["id"], {"data": {
            "id": locale["id"], "type": "betaBuildLocalizations", "attributes": {"whatsNew": notes}}})
    else:
        apple.request("POST", "betaBuildLocalizations", {"data": {
            "type": "betaBuildLocalizations", "attributes": {"locale": metadata["primaryLocale"], "whatsNew": notes},
            "relationships": {"build": {"data": {"type": "builds", "id": build_id}}}}})
    saved = apple.request("GET", base + "/betaBuildLocalizations")["data"]
    if not any(item["attributes"].get("locale") == metadata["primaryLocale"] and item["attributes"].get("whatsNew") == notes for item in saved):
        raise ValueError("Apple did not retain the build's testing notes")
    for group in groups:
        path = "betaGroups/" + group + "/relationships/builds"
        linked = apple.request("GET", path)["data"]
        if not any(item["id"] == build_id for item in linked):
            apple.request("POST", path, {"data": [{"type": "builds", "id": build_id}]})
        verified = apple.request("GET", path)["data"]
        if not any(item["id"] == build_id for item in verified):
            raise ValueError("Apple did not retain the beta group build assignment")
    return {"app": app_id, "build": build_id, "buildNumber": str(number), "notesVerified": True, "groupsVerified": True}


def submit(apple, number, metadata):
    result = prepare(apple, number, metadata)
    path = query("betaAppReviewSubmissions", build=result["build"])
    submissions = apple.request("GET", path)["data"]
    if not submissions:
        apple.request("POST", "betaAppReviewSubmissions", {"data": {"type": "betaAppReviewSubmissions",
            "relationships": {"build": {"data": {"type": "builds", "id": result["build"]}}}}})
        submissions = apple.request("GET", path)["data"]
    states = [item["attributes"]["betaReviewState"] for item in submissions]
    if len(states) != 1 or states[0] not in {"WAITING_FOR_REVIEW", "IN_REVIEW", "APPROVED"}:
        raise ValueError("Beta review is not in a successful submitted state: " + ", ".join(states))
    return {**result, "betaReviewState": states[0], "publicLinkEnabledByThisAction": False}


if __name__ == "__main__":
    from apple_accounts import Apple
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "submit"])
    parser.add_argument("--verified-run", required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    args = parser.parse_args()
    run = native_gate(args.verified_run)
    apple = Apple(args.key_file.read_bytes(), args.key_id, args.issuer)
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
    action = prepare if args.action == "prepare" else submit
    print(json.dumps(action(apple, run["run_number"], metadata)))
