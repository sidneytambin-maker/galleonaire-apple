"""Verify the successful release's exact build through Apple processing and beta access."""
import argparse
import base64
import json
import os
import time
from datetime import datetime, timezone

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build, checked_groups, query, submit


def configure_review_and_notifications(apple, app_id, build_id, notes):
    if not isinstance(notes, str) or not 20 <= len(notes) <= 4000:
        raise ValueError("Meaningful beta review notes are required")
    path = "apps/" + app_id + "/betaAppReviewDetail"
    review = apple.request("GET", path)["data"]
    # Existing owner contact details remain in Apple's record and are never logged.
    apple.request("PATCH", "betaAppReviewDetails/" + review["id"], {"data": {
        "type": "betaAppReviewDetails", "id": review["id"], "attributes": {"notes": notes}}})
    if apple.request("GET", path)["data"]["attributes"].get("notes") != notes:
        raise ValueError("Apple did not retain the beta review notes")
    path = "builds/" + build_id + "/buildBetaDetail"
    detail = apple.request("GET", path)["data"]
    apple.request("PATCH", "buildBetaDetails/" + detail["id"], {"data": {
        "type": "buildBetaDetails", "id": detail["id"], "attributes": {"autoNotifyEnabled": True}}})
    if apple.request("GET", path)["data"]["attributes"].get("autoNotifyEnabled") is not True:
        raise ValueError("Apple did not enable automatic beta notifications")


def wait_for_build(client, number, version, deadline):
    while True:
        try:
            return checked_build(client(), number, version)
        except ValueError as error:
            # Only missing/processing builds may be retried. Ownership, version,
            # expiry and encryption failures must never be bypassed.
            if str(error) not in {
                "The exact release build has not appeared in Apple processing yet",
                "The exact release build is still processing",
            } or time.monotonic() >= deadline:
                raise
            print("Waiting for the exact uploaded build to finish Apple processing.", flush=True)
            time.sleep(60)


def availability_snapshot(apple, app_id, build_id, number, metadata):
    detail = apple.request("GET", "builds/" + build_id + "/buildBetaDetail")["data"]["attributes"]
    reviews = apple.request("GET", query("betaAppReviewSubmissions", build=build_id))["data"]
    review_state = reviews[0]["attributes"]["betaReviewState"] if len(reviews) == 1 else None
    result = {"internalBuildState": detail.get("internalBuildState"),
              "externalBuildState": detail.get("externalBuildState"), "betaReviewState": review_state,
              "availableForTesting": False}
    if result["internalBuildState"] == result["externalBuildState"] == "IN_BETA_TESTING" and review_state == "APPROVED":
        if checked_build(apple, number, metadata["version"]) != (app_id, build_id):
            raise ValueError("The final availability read-back resolved a different build")
        groups = checked_groups(apple, app_id, metadata)
        for group in groups:
            linked = apple.request("GET", "betaGroups/" + group + "/relationships/builds")["data"]
            if not any(item["id"] == build_id for item in linked):
                raise ValueError("The available build is missing from an expected testing group")
        result.update(availableForTesting=True, groupIDs=groups, groupsVerified=True,
                      verifiedAt=datetime.now(timezone.utc).isoformat())
    return result


def pending_review_outcome(result):
    if (result.get("availableForTesting") is False and
            result.get("betaReviewState") in {"WAITING_FOR_REVIEW", "IN_REVIEW"} and
            result.get("externalBuildState") in {"WAITING_FOR_BETA_REVIEW", "IN_BETA_REVIEW"}):
        return {**result, "monitoringState": "AWAITING_APPLE_REVIEW"}
    raise TimeoutError("Apple availability is unresolved outside an ordinary pending review")


def complete(run_id):
    run = native_gate(run_id)
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
    key = base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True)
    def client():
        return Apple(key, os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app_id, build_id = wait_for_build(client, run["run_number"], metadata["version"], time.monotonic() + 1800)
    apple = client()
    locales = apple.request("GET", "apps/" + app_id + "/betaAppLocalizations")["data"]
    locale = next(item for item in locales if item["attributes"]["locale"] == metadata["primaryLocale"])
    apple.request("PATCH", "betaAppLocalizations/" + locale["id"], {"data": {
        "type": "betaAppLocalizations", "id": locale["id"], "attributes": {"description": metadata["description"]}}})
    saved = apple.request("GET", "apps/" + app_id + "/betaAppLocalizations")["data"]
    if not any(item["attributes"].get("locale") == metadata["primaryLocale"] and item["attributes"].get("description") == metadata["description"] for item in saved):
        raise ValueError("Apple did not retain the updated beta description")
    configure_review_and_notifications(apple, app_id, build_id, metadata["reviewNotes"])
    result = submit(client(), run["run_number"], metadata)
    result.update(version=metadata["version"], reviewNotesVerified=True, automaticNotificationsVerified=True,
                  groups=[metadata["internalGroup"], metadata["externalGroup"]])
    report = ROOT / "Artifacts/testflight-beta-status.json"
    report.parent.mkdir(exist_ok=True)
    deadline = time.monotonic() + 3600
    while True:
        apple = client()
        result.update(availability_snapshot(apple, app_id, build_id, run["run_number"], metadata))
        result.update(releaseRunId=str(run_id), releaseCommit=run["head_sha"])
        report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
        if result["availableForTesting"]:
            return result
        if result["externalBuildState"] in {"BETA_REJECTED", "EXPIRED", "FAILED"}:
            raise ValueError("Apple did not make this build available to external testers")
        if time.monotonic() >= deadline:
            result = pending_review_outcome(result)
            report.write_text(json.dumps(result, indent=2) + "\n")
            print("::notice::Apple beta review is pending. The uploaded build is unchanged; tester availability remains unconfirmed.", flush=True)
            print(json.dumps(result), flush=True)
            if os.environ.get("GITHUB_STEP_SUMMARY"):
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
                    summary.write("## TestFlight: awaiting Apple review\n\nThe preparation check finished normally. "
                                  "The release remains incomplete and tester availability is not confirmed.\n")
            return result
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-run", required=True)
    complete(parser.parse_args().verified_run)
