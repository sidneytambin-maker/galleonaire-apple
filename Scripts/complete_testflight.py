"""Verify the successful release's exact build through Apple processing and beta access."""
import argparse
import base64
import json
import os
import time

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from beta_release import checked_build, submit


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
    result = submit(client(), run["run_number"], metadata)
    report = ROOT / "Artifacts/testflight-beta-status.json"
    report.parent.mkdir(exist_ok=True)
    deadline = time.monotonic() + 3600
    while True:
        apple = client()
        detail = apple.request("GET", "builds/" + build_id + "/buildBetaDetail")["data"]["attributes"]
        result.update(internalBuildState=detail.get("internalBuildState"), externalBuildState=detail.get("externalBuildState"),
                      releaseRunId=str(run_id), releaseCommit=run["head_sha"])
        report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
        if result["internalBuildState"] == "IN_BETA_TESTING" and result["externalBuildState"] == "IN_BETA_TESTING":
            return result
        if result["externalBuildState"] in {"BETA_REJECTED", "EXPIRED", "FAILED"}:
            raise ValueError("Apple did not make this build available to external testers")
        if time.monotonic() >= deadline:
            raise TimeoutError("Apple beta review is still pending; the exact build and beta groups are recorded in the status report")
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-run", required=True)
    complete(parser.parse_args().verified_run)
