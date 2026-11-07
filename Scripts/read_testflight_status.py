"""Read the exact uploaded release's Apple state without changing distribution."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build, checked_groups
from complete_testflight import availability_snapshot

parser = argparse.ArgumentParser()
parser.add_argument("--verified-run", required=True)
args = parser.parse_args()
run = native_gate(args.verified_run)
metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
              os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
report = {"version": metadata["version"], "buildNumber": str(run["run_number"]),
          "releaseRunId": args.verified_run, "readAt": datetime.now(timezone.utc).isoformat()}
try:
    app_id, build_id = checked_build(apple, run["run_number"], metadata["version"])
except ValueError as error:
    if str(error) not in {"The exact release build has not appeared in Apple processing yet",
                          "The exact release build is still processing"}:
        raise
    report.update(processingState="PENDING", availableForTesting=False, detail=str(error))
else:
    report.update(app=app_id, build=build_id, processingState="VALID")
    report.update(availability_snapshot(apple, app_id, build_id, run["run_number"], metadata))
    groups = checked_groups(apple, app_id, metadata)
    report["groups"] = [{"name": name, "id": group,
        "containsBuild": any(item["id"] == build_id for item in
            apple.request("GET", "betaGroups/" + group + "/relationships/builds")["data"])}
        for name, group in zip([metadata["internalGroup"], metadata["externalGroup"]], groups)]
output = ROOT / "Artifacts/testflight-read-only-status.json"
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
