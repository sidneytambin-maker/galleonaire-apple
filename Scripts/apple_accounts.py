"""Galleonaire-only Apple registration and encrypted CI-secret provisioning."""
import argparse
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.serialization import pkcs12

BUNDLES = {"Phone": "com.sidneytambin.galleonaire", "Watch": "com.sidneytambin.galleonaire.watchkitapp"}
REPOSITORY = "sidneytambin-maker/galleonaire-apple"
TEAM = "HT5X86Q4DD"
ROOT = Path(__file__).resolve().parents[1]


def b64(data): return base64.urlsafe_b64encode(data).rstrip(b"=")


class Apple:
    def __init__(self, key, key_id, issuer):
        private = serialization.load_pem_private_key(key, password=None)
        now = int(time.time())
        header = b64(json.dumps({"alg": "ES256", "kid": key_id, "typ": "JWT"}).encode())
        claims = b64(json.dumps({"iss": issuer, "iat": now - 10, "exp": now + 1100, "aud": "appstoreconnect-v1"}).encode())
        body = header + b"." + claims
        r, s = decode_dss_signature(private.sign(body, ec.ECDSA(hashes.SHA256())))
        self.token = (body + b"." + b64(r.to_bytes(32, "big") + s.to_bytes(32, "big"))).decode()

    def request(self, method, path, body=None):
        request = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
                return json.loads(data) if data else None
        except urllib.error.HTTPError as error:
            response = json.loads(error.read())
            details = [{"status": e.get("status"), "code": e.get("code"), "detail": e.get("detail")} for e in response.get("errors", [])]
            raise RuntimeError(json.dumps(details)) from None


def gh(method, path, payload=None):
    cli = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
    command = [cli, "api", "--method", method, path]
    if payload is not None: command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None, text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def verify_environment():
    path = f"repos/{REPOSITORY}/environments/testflight"
    env = gh("GET", path)
    policies = gh("GET", path + "/deployment-branch-policies")
    assert env["deployment_branch_policy"] == {"protected_branches": False, "custom_branch_policies": True}, "Selected-branch protection required"
    assert [(p["name"], p["type"]) for p in policies["branch_policies"]] == [("main", "branch")], "Exactly the main branch must be permitted"


def secret(name, value):
    cli = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
    result = subprocess.run([cli, "secret", "set", name, "--repo", REPOSITORY, "--env", "testflight"], input=value, capture_output=True)
    if result.returncode: raise RuntimeError(f"Encrypted secret upload failed: {name}")
    print("Stored encrypted environment secret: " + name)


def register(apple):
    identifiers = {}
    for label, identifier in BUNDLES.items():
        found = apple.request("GET", "bundleIds?" + urllib.parse.urlencode({"filter[identifier]": identifier}))["data"]
        if found: record = found[0]
        else:
            record = apple.request("POST", "bundleIds", {"data": {"type": "bundleIds", "attributes": {"name": "Galleonaire " + label, "identifier": identifier, "platform": "IOS"}}})["data"]
        assert record["attributes"]["identifier"] == identifier
        identifiers[label] = record["id"]
        print("Registered: " + identifier)
    (ROOT / "Docs/Apple-Identifiers.json").write_text(json.dumps({"team": TEAM, "identifiers": {label: {"bundle": BUNDLES[label], "id": value} for label, value in identifiers.items()}}, indent=2) + "\n")
    return identifiers


def provision(apple, args, key_data):
    verify_environment()
    password = args.password_file.read_bytes().strip()
    p12 = args.certificate_file.read_bytes()
    private, certificate, chain = pkcs12.load_key_and_certificates(p12, password)
    assert private is not None and certificate is not None
    assert certificate.subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATIONAL_UNIT_NAME)[0].value == TEAM
    assert certificate.not_valid_after_utc.timestamp() > time.time() + 86400
    cert_der = certificate.public_bytes(serialization.Encoding.DER)
    certificates = apple.request("GET", "certificates?filter[certificateType]=DISTRIBUTION&limit=200")["data"]
    matched = [c for c in certificates if base64.b64decode(c["attributes"]["certificateContent"]) == cert_der]
    assert len(matched) == 1, "Existing distribution certificate must match Apple exactly"
    cert_id = matched[0]["id"]
    bundles = register(apple)
    profiles = {}
    for label, bundle_id in bundles.items():
        name = "Galleonaire " + label + " App Store"
        found = apple.request("GET", "profiles?" + urllib.parse.urlencode({"filter[name]": name, "filter[profileState]": "ACTIVE", "include": "bundleId,certificates", "limit": 200}))["data"]
        found = [p for p in found if p["relationships"]["bundleId"]["data"]["id"] == bundle_id and any(c["id"] == cert_id for c in p["relationships"]["certificates"]["data"])]
        if found: profile = found[0]
        else:
            profile = apple.request("POST", "profiles", {"data": {"type": "profiles", "attributes": {"name": name, "profileType": "IOS_APP_STORE"}, "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bundle_id}}, "certificates": {"data": [{"type": "certificates", "id": cert_id}]}}}})["data"]
        assert profile["attributes"]["profileState"] == "ACTIVE"
        profiles[label] = profile["attributes"]["profileContent"].encode()
    # The key, password, P12 and new profiles stay in memory locally. Only the
    # previously approved encrypted GitHub environment receives them.
    for label, value in profiles.items(): secret("APPLE_" + label.upper() + "_PROFILE_BASE64", value)
    secret("APPLE_DISTRIBUTION_P12_BASE64", base64.b64encode(p12))
    secret("APPLE_DISTRIBUTION_PASSWORD", password)
    secret("APP_STORE_CONNECT_KEY_BASE64", base64.b64encode(key_data))
    secret("APP_STORE_CONNECT_KEY_ID", args.key_id.encode())
    secret("APP_STORE_CONNECT_ISSUER_ID", args.issuer.encode())
    print("Galleonaire profiles and encrypted signing secrets configured; no local secret files created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "register", "provision"])
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--certificate-file", type=Path)
    parser.add_argument("--password-file", type=Path)
    args = parser.parse_args()
    key = args.key_file.read_bytes()
    client = Apple(key, args.key_id, args.issuer)
    if args.action == "register": register(client)
    elif args.action == "provision":
        assert args.certificate_file and args.password_file
        provision(client, args, key)
    else:
        apps = client.request("GET", "apps?" + urllib.parse.urlencode({"filter[bundleId]": BUNDLES["Phone"]}))["data"]
        print(json.dumps({"galleonaireApps": [{"id": app["id"], "name": app["attributes"]["name"], "bundleId": app["attributes"]["bundleId"]} for app in apps]}))
