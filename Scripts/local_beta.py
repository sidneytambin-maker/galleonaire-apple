"""Publish a local-signed build only after native, signature and Apple processing gates."""
import argparse
import json
from pathlib import Path

from beta_release import checked_build, checked_groups, submit
from beta_metadata import configure, resolve_app
from direct_upload import state
from local_sign import ROOT


def checked_upload(receipt, signing, upload, build_id):
    assert receipt["app"] == "6811170867"
    assert receipt["sha256"] == signing["ipaSHA256"]
    assert receipt["build"] == signing["build"] == upload["build"]
    assert receipt["uploaded"] is True and receipt["allPartChecksumsVerified"] is True
    assert signing["signatureInspectionComplete"] is True
    assert receipt["uploadId"] == upload["uploadId"]
    assert upload["state"]["state"] == "COMPLETE" and not upload["state"].get("errors")
    assert upload["buildResource"] == {"type": "builds", "id": build_id}


def availability(apple, number, metadata):
    app_id, build_id = checked_build(apple, number, metadata["version"])
    groups = checked_groups(apple, app_id, metadata)
    detail = apple.request("GET", "builds/" + build_id + "/buildBetaDetail")["data"]["attributes"]
    report = []
    for group_id in groups:
        group = apple.request("GET", "betaGroups/" + group_id)["data"]["attributes"]
        links = apple.request("GET", "betaGroups/" + group_id + "/relationships/builds")["data"]
        report.append({"name": group["name"], "containsBuild": any(b["id"] == build_id for b in links),
            "internal": group["isInternalGroup"], "publicLinkEnabled": group.get("publicLinkEnabled"),
            "publicLinkLimitEnabled": group.get("publicLinkLimitEnabled"), "publicLinkLimit": group.get("publicLinkLimit")})
    return {"app": app_id, "build": build_id, "buildNumber": str(number), "processingState": "VALID",
            "betaDetail": detail, "groups": report,
            "externalAvailable": detail.get("externalBuildState") == "IN_BETA_TESTING" and all(g["containsBuild"] for g in report)}


def execute(args):
    from apple_accounts import Apple
    from inspect_local_ipa import inspect

    directory = args.directory.resolve()
    apple = Apple(args.key_file.read_bytes(), args.key_id, args.issuer)
    assert resolve_app(apple) == "6811170867"
    metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_bytes())
    receipt = json.loads((directory / "direct-upload.json").read_bytes())
    if args.action == "publish":
        signing = inspect(directory, args.evidence.resolve(), args.openssl)
        upload = state(apple, receipt)
        app_id, build_id = checked_build(apple, receipt["build"], metadata["version"])
        checked_upload(receipt, signing, upload, build_id)
        contact = apple.request("GET", "apps/" + app_id + "/betaAppReviewDetail")["data"]["attributes"]
        configure(apple, metadata, contact)
        result = submit(apple, receipt["build"], metadata)
        (directory / "beta-submission.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
    result = availability(apple, receipt["build"], metadata)
    (directory / "beta-availability.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["publish", "status"])
    for name in ["directory", "evidence", "openssl", "key-file"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    execute(parser.parse_args())
