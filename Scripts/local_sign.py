"""Sign a natively validated archive locally without changing app code or cloud billing."""
import argparse
import base64
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path

from apple_accounts import Apple, BUNDLES, ROOT, TEAM, gh
from question_pack import check_pack, encoded


def validated_run(run_id, evidence):
    run = gh("GET", f"repos/sidneytambin-maker/galleonaire-apple/actions/runs/{run_id}")
    assert run["head_branch"] == "main" and run["path"] == ".github/workflows/testflight.yml"
    jobs = gh("GET", f"repos/sidneytambin-maker/galleonaire-apple/actions/runs/{run_id}/jobs")["jobs"]
    assert any(j["name"] == "validation" and j["conclusion"] == "success" for j in jobs), "Native validation must pass"
    git = ["git", "-c", "safe.directory=" + ROOT.as_posix()]
    subprocess.run(git + ["merge-base", "--is-ancestor", run["head_sha"], "HEAD"], cwd=ROOT, check=True, capture_output=True)
    changes = subprocess.check_output(git + ["diff", "--name-only", run["head_sha"], "--", "Apple", "Reference", "Scripts/ci.py", "Scripts/question_pack.py"], cwd=ROOT)
    assert not changes.strip(), "Native source or reviewed content changed after validation"
    for platform, count in [("iphone", 13), ("watch", 6)]:
        summary = json.loads((evidence / (platform + "-summary.log")).read_bytes())
        assert summary["result"] == "Passed" and summary["passedTests"] == count
        assert summary["failedTests"] == summary["skippedTests"] == 0
    core = (evidence / "core-tests.log").read_text()
    assert "Executed 38 tests, with 0 failures" in core
    return run


def decode_profile(data, openssl):
    result = subprocess.run([str(openssl), "cms", "-verify", "-binary", "-inform", "DER", "-noverify"],
                            input=data, capture_output=True)
    assert result.returncode == 0, "Provisioning profile CMS signature failed"
    return plistlib.loads(result.stdout)


def check_profile(profile, bundle, cert_der):
    assert profile["TeamIdentifier"] == [TEAM]
    assert profile["ExpirationDate"].timestamp() > time.time() + 86400
    assert not profile.get("ProvisionedDevices") and not profile.get("ProvisionsAllDevices")
    assert cert_der in profile["DeveloperCertificates"], "Distribution certificate not authorized by profile"
    entitlements = profile["Entitlements"]
    assert entitlements["application-identifier"] == TEAM + "." + bundle
    assert entitlements["com.apple.developer.team-identifier"] == TEAM
    assert entitlements["get-task-allow"] is False
    assert entitlements.get("beta-reports-active") is True
    return entitlements


def distribution_entitlements(bundle):
    assert bundle in BUNDLES.values()
    return {"application-identifier": TEAM + "." + bundle, "beta-reports-active": True,
            "com.apple.developer.team-identifier": TEAM, "get-task-allow": False}


def prepare_app(evidence, destination, build):
    source = evidence / "Galleonaire.xcarchive/Products/Applications/Galleonaire.app"
    if os.name == "nt":
        source = Path("\\\\?\\" + str(source.resolve()))
    assert not destination.exists(), "A fresh output directory is required"
    shutil.copytree(source, destination)
    expected = encoded(check_pack())
    for label, path in [("Phone", destination), ("Watch", destination / "Watch/GalleonaireWatch.app")]:
        info_path = path / "Info.plist"
        info = plistlib.loads(info_path.read_bytes())
        assert info["CFBundleIdentifier"] == BUNDLES[label]
        assert info["CFBundleDisplayName"] == "Galleonaire"
        assert info["CFBundleShortVersionString"] == "0.1.0"
        if label == "Watch":
            assert info["WKApplication"] and info["WKCompanionAppBundleIdentifier"] == BUNDLES["Phone"]
        banks = [p for p in path.rglob("questions.json") if ".app" not in p.relative_to(path).as_posix()]
        assert len(banks) == 1 and banks[0].read_bytes() == expected
        for sound in (ROOT / "Apple/App").glob("*.wav"):
            assert (path / sound.name).read_bytes() == sound.read_bytes()
        info["CFBundleVersion"] = str(build)
        info_path.write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY, sort_keys=False))
    return source


def make_ipa(app, output):
    executables = {p.parent / plistlib.loads(p.read_bytes())["CFBundleExecutable"]
                   for p in app.rglob("Info.plist") if p.parent.suffix == ".app"}
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for path in sorted(app.rglob("*")):
            assert not path.is_symlink(), "Unexpected symlink in mobile app"
            if not path.is_file():
                continue
            name = "Payload/Galleonaire.app/" + path.relative_to(app).as_posix()
            entry = zipfile.ZipInfo(name)
            entry.create_system = 3
            entry.external_attr = (0o100755 if path in executables else 0o100644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(entry, path.read_bytes())


def sign(args):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12

    evidence = args.evidence.resolve()
    run = validated_run(args.run, evidence)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    app = output / "Payload/Galleonaire.app"
    source = prepare_app(evidence, app, run["run_number"])
    password = args.password_file.read_bytes().strip()
    private, cert, chain = pkcs12.load_key_and_certificates(args.certificate_file.read_bytes(), password)
    assert private is not None and cert is not None
    assert cert.not_valid_after_utc.timestamp() > time.time() + 86400
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    apple = Apple(args.key_file.read_bytes(), args.key_id, args.issuer)
    certificates = apple.request("GET", "certificates?filter[certificateType]=DISTRIBUTION&limit=200")["data"]
    assert any(base64.b64decode(c["attributes"]["certificateContent"]) == cert_der for c in certificates)
    profile_report = {}
    with tempfile.TemporaryDirectory(prefix="galleonaire-", dir=args.key_file.parent) as temporary:
        temporary = Path(temporary)
        for label, bundle in BUNDLES.items():
            query = urllib.parse.urlencode({"filter[name]": "Galleonaire " + label + " App Store", "filter[profileState]": "ACTIVE", "limit": 200})
            found = apple.request("GET", "profiles?" + query)["data"]
            assert len(found) == 1 and found[0]["attributes"]["profileType"] == "IOS_APP_STORE"
            raw = base64.b64decode(found[0]["attributes"]["profileContent"])
            profile = decode_profile(raw, args.openssl)
            check_profile(profile, bundle, cert_der)
            bundle_path = app if label == "Phone" else app / "Watch/GalleonaireWatch.app"
            (bundle_path / "embedded.mobileprovision").write_bytes(raw)
            entitlements = distribution_entitlements(bundle)
            assert all(profile["Entitlements"].get(key) == value for key, value in entitlements.items())
            entitlement_file = label + ".plist"
            (temporary / entitlement_file).write_bytes(plistlib.dumps(entitlements))
            profile_report[label] = {"uuid": profile["UUID"], "bundle": bundle, "cmsVerified": True}
        log = bytearray()
        # Sign inside out with direct entitlements; avoid platform-dependent path scopes.
        for label, target in [("Watch", app / "Watch/GalleonaireWatch.app"), ("Phone", app)]:
            command = [str(args.rcodesign), "sign", "--shallow", "--p12-file", str(args.certificate_file),
                       "--p12-password-file", str(args.password_file), "--team-name", TEAM, "--timestamp-url", "none",
                       "--entitlements-xml-file", label + ".plist", str(target)]
            result = subprocess.run(command, cwd=temporary, capture_output=True)
            log.extend((result.stdout + result.stderr).replace(password, b"[REDACTED]"))
            (output / "signing.log").write_bytes(log)
            assert result.returncode == 0, "Local signing failed; inspect signing.log"
    (output / "distribution-certificate.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    ipa = output / "Galleonaire.ipa"
    make_ipa(app, ipa)
    receipt = {"validatedRun": args.run, "sourceRevision": run["head_sha"], "build": str(run["run_number"]),
               "version": "0.1.0", "ipaSHA256": hashlib.sha256(ipa.read_bytes()).hexdigest(), "profiles": profile_report,
               "signedLocally": True, "signer": "rcodesign 0.29.0", "codeDirectoryAlgorithms": "platform-derived",
               "signatureInspectionComplete": False, "uploaded": False}
    (output / "local-signing.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    for name in ["evidence", "output", "key-file", "certificate-file", "password-file", "rcodesign", "openssl"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--issuer", required=True)
    sign(parser.parse_args())
