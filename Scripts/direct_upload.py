"""Upload an independently verified local IPA with Apple's documented build API."""
import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

def upload_payload(app, build):
    return {"data": {"type": "buildUploads", "attributes": {"cfBundleShortVersionString": "0.1.0",
        "cfBundleVersion": str(build), "platform": "IOS"},
        "relationships": {"app": {"data": {"type": "apps", "id": app}}}}}


def file_payload(upload, size):
    assert size > 0
    return {"data": {"type": "buildUploadFiles", "attributes": {"assetType": "ASSET", "fileName": "Galleonaire.ipa",
        "fileSize": size, "uti": "com.apple.ipa"},
        "relationships": {"buildUpload": {"data": {"type": "buildUploads", "id": upload}}}}}


def commit_payload(file_id):
    # Apple's optional source checksums are not a substitute for its part ETags.
    return {"data": {"id": file_id, "type": "buildUploadFiles", "attributes": {"uploaded": True}}}


def chunk_matches(operation, payload):
    tag = (operation.get("entityTag") or "").strip('"').lower()
    start, length = operation["offset"], operation["length"]
    return tag == hashlib.md5(payload[start:start + length], usedforsecurity=False).hexdigest()


def checked_operations(operations, size):
    cursor = 0
    ordered = sorted(operations, key=lambda item: item["offset"])
    assert ordered
    for operation in ordered:
        assert operation["method"] == "PUT"
        assert operation["offset"] == cursor and operation["length"] > 0
        cursor += operation["length"]
        url = urllib.parse.urlparse(operation["url"])
        assert url.scheme == "https" and not url.username and not url.password and url.port in (None, 443)
        host = url.hostname or ""
        assert any(host.endswith(suffix) for suffix in (".apple.com", ".icloud-content.com", ".amazonaws.com")), "Unexpected Apple delivery host: " + host
        assert not any(h["name"].lower() in ("host", "cookie") for h in operation.get("requestHeaders", []))
    assert cursor == size, "Upload chunks must cover the IPA exactly once"
    return ordered


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        raise RuntimeError("Unexpected upload redirect; no bytes forwarded")


def transfer_bytes(operation, payload):
    start, length = operation["offset"], operation["length"]
    headers = {h["name"]: h["value"] for h in operation.get("requestHeaders", [])}
    request = urllib.request.Request(operation["url"], data=payload[start:start + length], headers=headers, method="PUT")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=180) as response:
            assert response.status in (200, 201, 204)
    except Exception as error:
        raise RuntimeError("Binary chunk upload failed (" + type(error).__name__ + "); signed URLs and headers withheld") from None


def saved(path, receipt):
    path.write_text(json.dumps(receipt, indent=2))


def state(apple, receipt):
    upload = apple.request("GET", "buildUploads/" + receipt["uploadId"] + "?include=build")["data"]
    assert upload["attributes"]["cfBundleVersion"] == receipt["build"]
    assert upload["attributes"]["cfBundleShortVersionString"] == "0.1.0"
    return {"build": receipt["build"], "uploadId": receipt["uploadId"], "state": upload["attributes"]["state"],
            "buildResource": upload.get("relationships", {}).get("build", {}).get("data")}


def execute(args):
    from apple_accounts import Apple
    from beta_metadata import resolve_app
    from inspect_local_ipa import inspect

    directory = args.directory.resolve()
    receipt_file = directory / "direct-upload.json"
    apple = Apple(args.key_file.read_bytes(), args.key_id, args.issuer)
    app = resolve_app(apple)
    assert app == "6811170867"
    if args.action == "status":
        print(json.dumps(state(apple, json.loads(receipt_file.read_bytes()))))
        return
    verified = inspect(directory, args.evidence.resolve(), args.openssl)
    payload = (directory / "Galleonaire.ipa").read_bytes()
    checksum = hashlib.sha256(payload).hexdigest()
    assert checksum == verified["ipaSHA256"] and verified["signatureInspectionComplete"]
    if receipt_file.exists():
        receipt = json.loads(receipt_file.read_bytes())
        assert receipt["sha256"] == checksum and receipt["build"] == verified["build"] and receipt["app"] == app
    else:
        upload = apple.request("POST", "buildUploads", upload_payload(app, verified["build"]))["data"]
        receipt = {"uploadId": upload["id"], "build": verified["build"], "app": app, "sha256": checksum, "uploaded": False}
        saved(receipt_file, receipt)
    if "fileId" not in receipt:
        files = apple.request("GET", "buildUploads/" + receipt["uploadId"] + "/buildUploadFiles")["data"]
        assert len(files) <= 1
        file = files[0] if files else apple.request("POST", "buildUploadFiles", file_payload(receipt["uploadId"], len(payload)))["data"]
        receipt["fileId"] = file["id"]
        saved(receipt_file, receipt)
    file = apple.request("GET", "buildUploadFiles/" + receipt["fileId"])["data"]
    attrs = file["attributes"]
    assert attrs["fileName"] == "Galleonaire.ipa" and attrs["fileSize"] == len(payload) and attrs["uti"] == "com.apple.ipa"
    delivery = attrs["assetDeliveryState"]["state"]
    assert delivery != "FAILED", "Apple rejected the file reservation"
    if delivery == "AWAITING_UPLOAD":
        for number, operation in enumerate(checked_operations(attrs["uploadOperations"], len(payload)), 1):
            if not chunk_matches(operation, payload):
                transfer_bytes(operation, payload)
                print("Uploaded binary chunk " + str(number), flush=True)
        confirmed = apple.request("GET", "buildUploadFiles/" + receipt["fileId"])["data"]["attributes"]
        operations = checked_operations(confirmed["uploadOperations"], len(payload))
        assert all(chunk_matches(operation, payload) for operation in operations), "Apple's received parts must match the IPA"
        receipt["allPartChecksumsVerified"] = True
        saved(receipt_file, receipt)
        apple.request("PATCH", "buildUploadFiles/" + receipt["fileId"], commit_payload(receipt["fileId"]))
    receipt["uploaded"] = True
    saved(receipt_file, receipt)
    verified["uploaded"] = True
    verified["uploadId"] = receipt["uploadId"]
    saved(directory / "local-signing.json", verified)
    print(json.dumps(state(apple, receipt)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["upload", "status"])
    for name in ["directory", "evidence", "openssl", "key-file"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    execute(parser.parse_args())
