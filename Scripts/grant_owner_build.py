"""Grant the verified existing account holder explicit access to the signed build."""
import base64
from datetime import datetime, timezone
import json
import os

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build, checked_groups
from diagnose_testflight_access import named_owner, pages


def main():
    run = native_gate("42338212510")
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
    apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
                  os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app_id, build_id = checked_build(apple, run["run_number"], metadata["version"])
    owner_group = checked_groups(apple, app_id, metadata)[0]
    users = pages(apple, "users?limit=200")
    holders = [u for u in users if named_owner(u) and "ACCOUNT_HOLDER" in u["attributes"].get("roles", [])]
    if len(holders) != 1:
        raise ValueError("Exactly one matching existing account holder is required")
    address = (holders[0]["attributes"].get("username") or "").strip().casefold()
    testers = pages(apple, "betaGroups/" + owner_group + "/betaTesters?limit=200")
    owners = [t for t in testers if named_owner(t) and address and
              (t["attributes"].get("email") or "").strip().casefold() == address]
    if len(owners) != 1 or owners[0]["attributes"].get("state") not in {"ACCEPTED", "INSTALLED"}:
        raise ValueError("Exactly one accepted existing owner tester is required")
    detail = apple.request("GET", "builds/" + build_id + "/buildBetaDetail")["data"]["attributes"]
    if detail.get("internalBuildState") != "IN_BETA_TESTING":
        raise ValueError("The exact build is not active for internal testing")
    tester_id = owners[0]["id"]
    path = "builds/" + build_id + "/relationships/individualTesters"
    linked = pages(apple, path + "?limit=200")
    result = {"readAt": datetime.now(timezone.utc).isoformat(), "version": metadata["version"],
              "buildNumber": str(run["run_number"]), "existingOwnerIdentityVerified": True,
              "deviceVisibilityVerified": False, "alreadyIndividuallyAssigned": any(t["id"] == tester_id for t in linked)}
    if not result["alreadyIndividuallyAssigned"]:
        try:
            apple.request("POST", path, {"data": [{"type": "betaTesters", "id": tester_id}]})
            result["assignmentAccepted"] = True
        except RuntimeError as error:
            # Apple errors can contain private tester data; emit only status/code.
            details = json.loads(str(error))
            result["assignmentAccepted"] = False
            result["appleErrors"] = [{"status": e.get("status"), "code": e.get("code")} for e in details]
    linked = pages(apple, path + "?limit=200")
    result["individualAssignmentVerified"] = any(t["id"] == tester_id for t in linked)
    result["groupAssignmentPreserved"] = any(b["id"] == build_id for b in
        pages(apple, "betaGroups/" + owner_group + "/relationships/builds?limit=200"))
    output = ROOT / "Artifacts/testflight-owner-assignment.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
