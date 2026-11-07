"""Persist exact-build Apple availability after review, without changing distribution."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build
from complete_testflight import availability_snapshot


def record_availability(evidence_path, status_path, snapshot, run):
    if snapshot.get("availableForTesting") is not True:
        return False
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    release = evidence["release"]
    previous = evidence["appleAvailability"]
    required = {
        "version": release["version"], "buildNumber": release["build"],
        "app": previous["app"], "build": previous["build"],
        "processingState": "VALID", "betaReviewState": "APPROVED",
        "internalBuildState": "IN_BETA_TESTING", "externalBuildState": "IN_BETA_TESTING",
        "groupsVerified": True,
    }
    if any(snapshot.get(key) != value for key, value in required.items()):
        raise ValueError("Availability evidence does not match the approved release")
    if (str(run["id"]) != str(release["workflowRun"]) or
            run["head_sha"] != release["commit"] or
            str(run["run_number"]) != release["build"]):
        raise ValueError("Availability resolved a different signed release")
    expected_groups = {group["id"] for group in previous["groups"]}
    if len(expected_groups) != 2 or set(snapshot.get("groupIDs", [])) != expected_groups:
        raise ValueError("Availability did not verify both existing groups")
    verified_at = snapshot.get("verifiedAt")
    if not verified_at or datetime.fromisoformat(verified_at).tzinfo is None:
        raise ValueError("An explicit verification time is required")
    status = status_path.read_text(encoding="utf-8")
    marker = "Exam Mode provides all ten subjects"
    if marker not in status or not status.startswith("# Release 42:"):
        raise ValueError("Release status changed; refusing to overwrite another release")
    snapshot = dict(snapshot)
    snapshot["groups"] = [{"name": group["name"], "id": group["id"], "containsBuild": True}
                          for group in previous["groups"]]
    evidence["appleAvailability"] = snapshot
    lead = (
        "# Release 42: 7 November 2026\n\n"
        "Galleonaire 0.2.0 (42) is APPROVED and IN_BETA_TESTING internally and externally.\n"
        "The exact valid, unexpired, export-compliant build is assigned to Owner Testing\n"
        "and Community Beta. Apple reports testing active for both groups.\n"
        f"Apple availability and both group memberships were read back at {verified_at}.\n"
        "Apple beta review is complete. The owner's on-device TestFlight listing has\n"
        "not been directly observed; server distribution status is not a device check.\n\n"
    )
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    status_path.write_text(lead + marker + status.split(marker, 1)[1], encoding="utf-8")
    return True


def main(run_id):
    run = native_gate(run_id)
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
    apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
                  os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app_id, build_id = checked_build(apple, run["run_number"], metadata["version"])
    snapshot = {"version": metadata["version"], "buildNumber": str(run["run_number"]),
                "app": app_id, "build": build_id, "processingState": "VALID",
                "releaseRunId": str(run_id), "releaseCommit": run["head_sha"],
                "readAt": datetime.now(timezone.utc).isoformat(),
                "buildValidUnexpiredAndCompliant": True, "deviceVisibilityVerified": False}
    snapshot.update(availability_snapshot(apple, app_id, build_id, run["run_number"], metadata))
    if os.environ.get("GITHUB_RUN_ID"):
        snapshot["availabilityWorkflowURL"] = (
            "https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/" + os.environ["GITHUB_RUN_ID"])
    artifact = ROOT / "Artifacts/testflight-persistent-status.json"
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(json.dumps(snapshot), flush=True)
    completed = record_availability(ROOT / "Docs/Release-42-Verification.json",
                                    ROOT / "Docs/Release-Status.md", snapshot, run)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
            summary.write("## TestFlight 0.2.0 (42)\n\n" + (
                "Apple reports testing active for both groups. Device visibility has not been observed.\n"
                if completed else
                "Awaiting Apple approval or distribution. The release is incomplete; this successful check does not mean tester availability.\n"))
            summary.write("\nApple review state: " + str(snapshot.get("betaReviewState")) + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write("completed=" + str(completed).lower() + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-run", required=True)
    main(parser.parse_args().verified_run)
