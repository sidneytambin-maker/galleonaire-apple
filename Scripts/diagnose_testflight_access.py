"""Read tester access without publishing tester names, addresses or identifiers."""
import base64
from collections import Counter
from datetime import datetime, timezone
import json
import os
from urllib.parse import urlparse

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build, checked_groups
from complete_testflight import availability_snapshot


def pages(apple, path):
    result = []
    while path:
        page = apple.request("GET", path)
        result.extend(page["data"])
        link = page.get("links", {}).get("next")
        if not link:
            break
        parsed = urlparse(link)
        if parsed.netloc != "api.appstoreconnect.apple.com" or not parsed.path.startswith("/v1/"):
            raise ValueError("Unexpected Apple pagination host")
        path = parsed.path[4:] + ("?" + parsed.query if parsed.query else "")
    return result


def named_owner(item):
    attributes = item["attributes"]
    return ((attributes.get("firstName") or "").strip().casefold() == "sidney" and
            (attributes.get("lastName") or "").strip().casefold() == "tambin")


def main():
    run = native_gate("42338212510")
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
    apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
                  os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app_id, build_id = checked_build(apple, run["run_number"], metadata["version"])
    report = {"readAt": datetime.now(timezone.utc).isoformat(), "app": app_id,
              "version": metadata["version"], "buildNumber": str(run["run_number"]),
              "deviceAccountIdentityVerified": False}
    report.update(availability_snapshot(apple, app_id, build_id, run["run_number"], metadata))
    holder_emails = set()
    try:
        users = pages(apple, "users?limit=200")
        holders = [u for u in users if "ACCOUNT_HOLDER" in u["attributes"].get("roles", [])]
        holder_emails = {(u["attributes"].get("username") or "").strip().casefold() for u in holders}
        holder_emails.discard("")
        report["accountHolderLookup"] = {"available": True, "count": len(holders),
                                          "namedOwnerCount": sum(named_owner(u) for u in holders)}
    except RuntimeError:
        report["accountHolderLookup"] = {"available": False}
    group_ids = checked_groups(apple, app_id, metadata)
    report["groups"] = []
    for name, group_id in zip([metadata["internalGroup"], metadata["externalGroup"]], group_ids):
        group = apple.request("GET", "betaGroups/" + group_id)["data"]["attributes"]
        testers = pages(apple, "betaGroups/" + group_id + "/betaTesters?limit=200")
        builds = pages(apple, "betaGroups/" + group_id + "/builds?limit=200")
        owners = [t for t in testers if named_owner(t) or
                  (t["attributes"].get("email") or "").strip().casefold() in holder_emails]
        owner_details = []
        for tester in owners:
            attributes = tester["attributes"]
            memberships = pages(apple, "betaTesters/" + tester["id"] + "/betaGroups?limit=200")
            individual = pages(apple, "betaTesters/" + tester["id"] + "/builds?limit=200")
            owner_details.append({"nameMatchesOwner": named_owner(tester),
                "emailMatchesAccountHolder": (attributes.get("email") or "").strip().casefold() in holder_emails,
                "state": attributes.get("state"), "inviteType": attributes.get("inviteType"),
                "expectedGroupMemberships": [g["attributes"]["name"] for g in memberships if g["id"] in group_ids],
                "individuallyAssignedBuildNumbers": [b["attributes"]["version"] for b in individual]})
        report["groups"].append({"name": name, "isInternalGroup": group.get("isInternalGroup"),
            "containsBuild42": any(b["id"] == build_id for b in builds),
            "containsBuild27": any(b["attributes"].get("version") == "27" for b in builds),
            "hasAccessToAllBuilds": group.get("hasAccessToAllBuilds"),
            "publicLinkEnabled": group.get("publicLinkEnabled"),
            "testerCount": len(testers), "testerStates": dict(Counter(t["attributes"].get("state") for t in testers)),
            "anonymousTesterCount": sum(not t["attributes"].get("email") for t in testers),
            "ownerMatches": owner_details})
    build = apple.request("GET", "builds/" + build_id)["data"]["attributes"]
    report["build"] = {k: build.get(k) for k in ["version", "processingState", "expired", "minOsVersion", "buildAudienceType", "uploadedDate"]}
    detail = apple.request("GET", "builds/" + build_id + "/buildBetaDetail")["data"]["attributes"]
    report["automaticNotificationsEnabled"] = detail.get("autoNotifyEnabled")
    localizations = apple.request("GET", "builds/" + build_id + "/betaBuildLocalizations")["data"]
    report["testingNotesMatch"] = any(x["attributes"].get("locale") == metadata["primaryLocale"] and
                                     x["attributes"].get("whatsNew") == metadata["whatToTest"] for x in localizations)
    output = ROOT / "Artifacts/testflight-access-diagnosis.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
