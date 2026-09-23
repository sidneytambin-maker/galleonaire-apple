"""Verify local signatures and retain the exact tested native code and resources."""
import argparse
import hashlib
import json
import os
import plistlib
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from local_sign import BUNDLES, TEAM, ROOT, check_profile, decode_profile, distribution_entitlements, validated_run
from macho_seals import check_bundle, signature_blobs, slices
from question_pack import check_pack, encoded


def native_sections(data):
    wide = data[:4] == b"\xcf\xfa\xed\xfe"
    assert wide or data[:4] == b"\xce\xfa\xed\xfe"
    cursor = 32 if wide else 28
    sections = []
    for _ in range(struct.unpack_from("<I", data, 16)[0]):
        command, length = struct.unpack_from("<II", data, cursor)
        assert length >= 8 and cursor + length <= len(data)
        if command in (1, 0x19):
            segment_wide = command == 0x19
            count = struct.unpack_from("<I", data, cursor + (64 if segment_wide else 48))[0]
            section = cursor + (72 if segment_wide else 56)
            for _ in range(count):
                name = data[section:section + 32]
                address, size = struct.unpack_from("<QQ" if segment_wide else "<II", data, section + 32)
                offset = struct.unpack_from("<I", data, section + (48 if segment_wide else 40))[0]
                flags = struct.unpack_from("<I", data, section + (64 if segment_wide else 56))[0]
                empty = flags & 0xff in (1, 0xc, 0x12)
                assert empty or offset + size <= len(data)
                digest = None if empty else hashlib.sha256(data[offset:offset + size]).hexdigest()
                sections.append((name, address, size, flags, digest))
                section += 80 if segment_wide else 68
        cursor += length
    assert sections
    return sections


def cms_signature(blobs, certificate, openssl, directory, bundle):
    assert {0, 2, 5, 7, 0x10000} <= set(blobs), "Full CMS, requirements and XML/DER entitlements required"
    cd = blobs[0]
    flags, identifier_offset = struct.unpack_from(">I", cd, 12)[0], struct.unpack_from(">I", cd, 20)[0]
    assert not flags & 2, "Ad-hoc signatures cannot be distributed"
    assert cd[identifier_offset:].split(b"\0", 1)[0].decode() == bundle
    assert struct.unpack_from(">I", cd, 8)[0] >= 0x20200
    team_offset = struct.unpack_from(">I", cd, 48)[0]
    assert cd[team_offset:].split(b"\0", 1)[0].decode() == TEAM
    (directory / "cd.bin").write_bytes(cd)
    (directory / "signature.der").write_bytes(blobs[0x10000][8:])
    result = subprocess.run([str(openssl), "cms", "-verify", "-binary", "-inform", "DER",
        "-in", str(directory / "signature.der"), "-content", str(directory / "cd.bin"),
        "-nointern", "-certfile", str(certificate), "-noverify"], capture_output=True)
    assert result.returncode == 0, "CMS signer/digest verification failed"
    assert result.stdout == cd, "CMS verification must return the exact signed CodeDirectory"


def inspect(directory, evidence, openssl):
    receipt_path = directory / "local-signing.json"
    receipt = json.loads(receipt_path.read_bytes())
    run = validated_run(receipt["validatedRun"], evidence)
    assert receipt["sourceRevision"] == run["head_sha"] and receipt["build"] == str(run["run_number"])
    ipa = directory / "Galleonaire.ipa"
    assert hashlib.sha256(ipa.read_bytes()).hexdigest() == receipt["ipaSHA256"]
    certificate = directory / "distribution-certificate.pem"
    cert_der = x509.load_pem_x509_certificate(certificate.read_bytes()).public_bytes(serialization.Encoding.DER)
    source = evidence / "Galleonaire.xcarchive/Products/Applications/Galleonaire.app"
    if os.name == "nt":
        source = Path("\\\\?\\" + str(source.resolve()))
    expected_questions = encoded(check_pack())
    reports = []
    with zipfile.ZipFile(ipa) as package, tempfile.TemporaryDirectory() as temporary:
        assert package.testzip() is None
        names = package.namelist()
        assert len(names) == len(set(names))
        assert all(n.startswith("Payload/Galleonaire.app/") and ".." not in Path(n).parts for n in names)
        assert not any(n.lower().endswith((".p8", ".p12", ".pem")) for n in names)
        for label, relative in [("Phone", ""), ("Watch", "Watch/GalleonaireWatch.app/")]:
            prefix = "Payload/Galleonaire.app/" + relative
            info = plistlib.loads(package.read(prefix + "Info.plist"))
            assert info["CFBundleIdentifier"] == BUNDLES[label]
            assert info["CFBundleDisplayName"] == "Galleonaire"
            assert info["CFBundleVersion"] == receipt["build"] and info["CFBundleShortVersionString"] == "0.1.0"
            if label == "Watch":
                assert info["WKApplication"] and info["WKCompanionAppBundleIdentifier"] == BUNDLES["Phone"]
            original_info = plistlib.loads((source / relative / "Info.plist").read_bytes())
            original_info["CFBundleVersion"] = receipt["build"]
            assert info == original_info, "Only the distribution build number may change"
            profile = decode_profile(package.read(prefix + "embedded.mobileprovision"), openssl)
            check_profile(profile, BUNDLES[label], cert_der)
            assert profile["UUID"] == receipt["profiles"][label]["uuid"]
            binary = package.read(prefix + info["CFBundleExecutable"])
            original = (source / relative / info["CFBundleExecutable"]).read_bytes()
            signed_slices, source_slices = list(slices(binary)), list(slices(original))
            assert len(signed_slices) == len(source_slices)
            for signed, unsigned in zip(signed_slices, source_slices):
                assert signed[4:12] == unsigned[4:12], "Native architecture changed"
                assert native_sections(signed) == native_sections(unsigned), "Tested native code/data changed"
                blobs = signature_blobs(signed)
                if label == "Watch":
                    assert blobs[0][37] == 1 and blobs.get(0x1000, b"")[37:38] == b"\x02", "Watch must retain Xcode's dual SHA1/SHA256 directories"
                entitlement = plistlib.loads(blobs[5][8:])
                assert entitlement == distribution_entitlements(BUNDLES[label]), "Only this app's required distribution entitlements are permitted"
                cms_signature(blobs, certificate, openssl, Path(temporary), BUNDLES[label])
            report = check_bundle(package, prefix)
            assert not report["failures"], "Signed content seal failed"
            own = [n for n in names if n.startswith(prefix) and ".app/" not in n[len(prefix):]]
            banks = [n for n in own if n.endswith("questions.json")]
            assert len(banks) == 1 and package.read(banks[0]) == expected_questions
            assert prefix + "Assets.car" in names and prefix + "PrivacyInfo.xcprivacy" in names
            reports.append({**report, "cmsSignerVerified": True, "nativeSectionsUnchanged": True, "questions": 600})
        changed_metadata = {"Info.plist", "Watch/GalleonaireWatch.app/Info.plist"}
        binaries = {"Galleonaire", "Watch/GalleonaireWatch.app/GalleonaireWatch"}
        for file in source.rglob("*"):
            if not file.is_file():
                continue
            relative = file.relative_to(source).as_posix()
            if relative in changed_metadata | binaries or "_CodeSignature/" in relative:
                continue
            assert package.read("Payload/Galleonaire.app/" + relative) == file.read_bytes(), relative + " changed"
    receipt["signatureInspectionComplete"] = True
    receipt["signatureChecks"] = reports
    receipt["nativePlatformTrustVerification"] = "Independent content/CMS verification only; Apple processing and beta availability are recorded separately"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ["directory", "evidence", "openssl"]:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    inspect(args.directory.resolve(), args.evidence.resolve(), args.openssl)
