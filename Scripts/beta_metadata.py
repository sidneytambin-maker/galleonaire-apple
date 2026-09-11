"""Configure Galleonaire beta information only after a verified native release run."""
import argparse
import json
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path

from release import BUNDLES, ROOT

REPOSITORY = "sidneytambin-maker/galleonaire-apple"


def resolve_app(apple):
    response = apple.request("GET", "apps?" + urllib.parse.urlencode({"filter[bundleId]": BUNDLES["Phone"]}))
    apps = response["data"]
    if len(apps) != 1:
        raise ValueError("Create the Galleonaire app record in App Store Connect first")
    app = apps[0]
    if app["attributes"].get("bundleId") != BUNDLES["Phone"] or app["attributes"].get("name") != "Galleonaire":
        raise ValueError("Refusing to configure another app or an unexpected product name")
    return app["id"]


def native_gate(run):
    if not re.fullmatch(r"[0-9]+", run): raise ValueError("A GitHub run number is required")
    cli = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
    result = json.loads(subprocess.check_output([cli, "api", f"repos/{REPOSITORY}/actions/runs/{run}"]))
    if result["conclusion"] != "success" or result["head_branch"] != "main" or result["path"] != ".github/workflows/testflight.yml":
        raise ValueError("The full main-branch TestFlight Release workflow must pass first")
    git = ["git", "-c", "safe.directory=" + ROOT.as_posix()]
    subprocess.run(git + ["merge-base", "--is-ancestor", result["head_sha"], "HEAD"], cwd=ROOT, check=True, capture_output=True)
    changed = subprocess.check_output(git + ["diff", "--name-only", result["head_sha"], "HEAD", "--", "Apple", "Scripts/ci.py", "Scripts/release.py", ".github/workflows/testflight.yml"], cwd=ROOT)
    if changed.strip(): raise ValueError("The native or release code changed after the verified run")


def review_fields(metadata, contact):
    phone = contact.get("contactPhone", "")
    if not isinstance(phone, str) or not re.fullmatch(r"\+?[0-9 ()-]{7,30}", phone):
        raise ValueError("A valid owner-supplied review contact number is required")
    for key in ["description", "whatToTest", "reviewNotes"]:
        if not isinstance(metadata.get(key), str) or not 20 <= len(metadata[key]) <= 4000:
            raise ValueError("Missing or oversized beta metadata: " + key)
    if metadata.get("name") != "Galleonaire": raise ValueError("Unexpected beta app name")
    return {"contactFirstName": "Sidney", "contactLastName": "Tambin", "contactEmail": metadata["feedbackEmail"],
            "contactPhone": phone, "demoAccountRequired": False, "notes": metadata["reviewNotes"]}


def configure(apple, metadata, contact):
    app_id = resolve_app(apple)
    fields = review_fields(metadata, contact)
    base = "apps/" + app_id
    localizations = apple.request("GET", base + "/betaAppLocalizations")["data"]
    groups = apple.request("GET", "betaGroups?" + urllib.parse.urlencode({"filter[app]": app_id}))["data"]
    review = apple.request("GET", base + "/betaAppReviewDetail")["data"]
    desired_groups = [(metadata["internalGroup"], True), (metadata["externalGroup"], False)]
    for name, internal in desired_groups:
        matches = [g for g in groups if g["attributes"]["name"] == name]
        if len(matches) > 1 or any(g["attributes"].get("isInternalGroup") != internal for g in matches):
            raise ValueError("A beta group has an unexpected identity")
    intended = {"description": metadata["description"], "feedbackEmail": metadata["feedbackEmail"]}
    locale = next((item for item in localizations if item["attributes"]["locale"] == metadata["primaryLocale"]), None)
    if locale:
        apple.request("PATCH", "betaAppLocalizations/" + locale["id"], {"data": {"id": locale["id"], "type": "betaAppLocalizations", "attributes": intended}})
    else:
        apple.request("POST", "betaAppLocalizations", {"data": {"type": "betaAppLocalizations", "attributes": {"locale": metadata["primaryLocale"], **intended},
                      "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})
    apple.request("PATCH", "betaAppReviewDetails/" + review["id"], {"data": {"id": review["id"], "type": "betaAppReviewDetails", "attributes": fields}})
    for name, internal in desired_groups:
        if not any(g["attributes"]["name"] == name for g in groups):
            apple.request("POST", "betaGroups", {"data": {"type": "betaGroups", "attributes": {"name": name, "isInternalGroup": internal,
                          "hasAccessToAllBuilds": False, "feedbackEnabled": True, "publicLinkEnabled": False},
                          "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})
    saved = apple.request("GET", base + "/betaAppLocalizations")["data"]
    saved_locale = next(item for item in saved if item["attributes"]["locale"] == metadata["primaryLocale"])
    if any(saved_locale["attributes"].get(key) != value for key, value in intended.items()): raise ValueError("Apple did not retain beta metadata")
    saved_review = apple.request("GET", base + "/betaAppReviewDetail")["data"]["attributes"]
    if any(saved_review.get(key) != value for key, value in fields.items()): raise ValueError("Apple did not retain review information")
    saved_groups = apple.request("GET", "betaGroups?" + urllib.parse.urlencode({"filter[app]": app_id}))["data"]
    if any(not any(g["attributes"]["name"] == name and g["attributes"].get("isInternalGroup") == internal for g in saved_groups) for name, internal in desired_groups):
        raise ValueError("Apple did not retain beta groups")
    return {"app": app_id, "metadataVerified": True, "groupsVerified": True, "reviewSubmitted": False, "testersInvited": False}


if __name__ == "__main__":
    from apple_accounts import Apple
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-run", required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--contact-file", type=Path, required=True)
    args = parser.parse_args()
    native_gate(args.verified_run)
    client = Apple(args.key_file.read_bytes(), args.key_id, args.issuer)
    result = configure(client, json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text()), json.loads(args.contact_file.read_bytes()))
    print(json.dumps(result))
