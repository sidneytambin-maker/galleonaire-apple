"""Sign, inspect and upload Galleonaire on an ephemeral Apple build runner."""
import argparse
import base64
import datetime
import hashlib
import json
import os
import plistlib
import re
import secrets
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from ci import ARTIFACTS, ROOT, run, select_xcode, verify_archive
from question_pack import check_pack, encoded

TEAM = "HT5X86Q4DD"
BUNDLES = {"Phone": "com.sidneytambin.galleonaire", "Watch": "com.sidneytambin.galleonaire.watchkitapp"}
AUDIO = ("magical-library", "selected", "locked", "correct", "incorrect", "lifelineSelected", "lifelineActivated", "lifelineResult", "nextQuestion", "milestone", "majorMilestone", "finalQuestion", "victory", "fiftyFifty", "audience", "swapQuestion")
EXAM_BANK = ROOT / "Apple/Sources/GalleonaireCore/Resources/exam-bank.json"


def configured_version(specification, request, metadata):
    version = str(specification["settings"]["base"]["MARKETING_VERSION"])
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version), "A three-part release version is required"
    assert version == request["version"] == metadata["version"], "Project, release request and TestFlight versions must agree"
    return version


def quiet(command):
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"Signing command failed: {Path(command[0]).name} {command[1]}")
    return result.stdout


def secret_file(path, data):
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(data)
    return path


def decode_profile(path, expected_bundle):
    profile = plistlib.loads(quiet(["security", "cms", "-D", "-i", str(path)]))
    entitlement = profile["Entitlements"]
    assert profile["TeamIdentifier"] == [TEAM]
    assert entitlement["application-identifier"] == TEAM + "." + expected_bundle
    assert entitlement.get("get-task-allow") is False
    assert not profile.get("ProvisionedDevices") and not profile.get("ProvisionsAllDevices")
    assert profile["ExpirationDate"] > datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return profile


def inspect_ipa(ipa, build, temporary, version):
    classic = check_pack()
    expected_questions = encoded(classic)
    expected_exam = EXAM_BANK.read_bytes()
    exam = json.loads(expected_exam)
    with zipfile.ZipFile(ipa) as package:
        names = package.namelist()
        phone = "Payload/Galleonaire.app/"
        watch = phone + "Watch/GalleonaireWatch.app/"
        for prefix, bundle in [(phone, BUNDLES["Phone"]), (watch, BUNDLES["Watch"])]:
            info = plistlib.loads(package.read(prefix + "Info.plist"))
            assert info["CFBundleIdentifier"] == bundle
            assert info["CFBundleDisplayName"] == "Galleonaire"
            assert info["CFBundleVersion"] == build
            assert info["CFBundleShortVersionString"] == version, "Each app must match the configured release version"
            resources = [name[len(prefix):] for name in names if name.startswith(prefix) and ".app/" not in name[len(prefix):]]
            banks = [name for name in resources if name.endswith("questions.json")]
            assert len(banks) == 1, "Each app needs exactly one question bank"
            assert package.read(prefix + banks[0]) == expected_questions, "Each app must contain the identical reviewed 1000-question bank"
            exam_banks = [name for name in resources if name.endswith("exam-bank.json")]
            assert len(exam_banks) == 1, "Each app needs exactly one exam bank"
            assert package.read(prefix + exam_banks[0]) == expected_exam, "Each app must contain the identical reviewed exam bank"
            assert all(name + ".wav" in resources for name in AUDIO), "Each app needs the complete audio collection"
            assert prefix + "Assets.car" in names
            assert prefix + "PrivacyInfo.xcprivacy" in names
            assert prefix + "_CodeSignature/CodeResources" in names
            profile_path = secret_file(temporary / ("check-" + bundle + ".mobileprovision"), package.read(prefix + "embedded.mobileprovision"))
            decode_profile(profile_path, bundle)
        watch_info = plistlib.loads(package.read(watch + "Info.plist"))
        assert watch_info["WKApplication"] is True
        assert watch_info["WKCompanionAppBundleIdentifier"] == BUNDLES["Phone"]
        assert not any(name.lower().endswith((".p8", ".p12", ".pem")) for name in names)
    original_ids = {question["id"] for question in classic["questions"]}
    added_ids = {item["question"]["id"] for item in exam["items"]} - original_ids
    report = {"name": "Galleonaire", "version": version, "build": build, "phoneBundle": BUNDLES["Phone"], "watchBundle": BUNDLES["Watch"],
              "watchEmbedded": True, "questionCountPerApp": len(original_ids) + len(added_ids),
              "originalQuestionCountPerApp": len(original_ids), "additionalQuestionCountPerApp": len(added_ids),
              "examEligibleQuestionCountPerApp": len(exam["items"]), "questionBanksMatchReviewedSource": True,
              "examBanksMatchReviewedSource": True, "questionBankSHA256": hashlib.sha256(expected_questions).hexdigest(),
              "examBankSHA256": hashlib.sha256(expected_exam).hexdigest(),
              "distributionProfilesVerified": True, "uploaded": False}
    (ARTIFACTS / "signed-package-verification.json").write_text(json.dumps(report, indent=2))
    return report


def release(build, upload):
    import yaml

    assert re.fullmatch(r"[1-9][0-9]*", build), "Positive integer build number required"
    assert os.environ.get("GITHUB_REPOSITORY") == "sidneytambin-maker/galleonaire-apple"
    assert os.environ.get("GITHUB_REF") == "refs/heads/main", "Only the approved main branch may release"
    select_xcode()
    ARTIFACTS.mkdir(exist_ok=True)
    specification = yaml.safe_load((ROOT / "Apple/project.yml").read_text())
    version = configured_version(specification, json.loads((ROOT / "Docs/Release-Request.json").read_text()),
                                 json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text()))
    with tempfile.TemporaryDirectory(prefix="galleonaire-signing-", dir=os.environ.get("RUNNER_TEMP")) as directory:
        temporary = Path(directory)
        os.chmod(temporary, 0o700)
        keychain = temporary / "build.keychain-db"
        keychain_password = secrets.token_urlsafe(32)
        installed_profiles = []
        signing_spec = ROOT / "Apple/SigningProject.json"
        keychain_created = False
        original_keychains = quiet(["security", "list-keychains", "-d", "user"]).decode()
        original_paths = re.findall(r'"([^"]+)"', original_keychains)
        try:
            certificate = secret_file(temporary / "distribution.p12", base64.b64decode(os.environ["APPLE_DISTRIBUTION_P12_BASE64"], validate=True))
            if upload:
                private_keys = temporary / "private_keys"
                private_keys.mkdir(mode=0o700)
                key_id = os.environ["APP_STORE_CONNECT_KEY_ID"]
                assert re.fullmatch(r"[A-Z0-9]+", key_id)
                secret_file(private_keys / f"AuthKey_{key_id}.p8", base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True))
                os.environ["API_PRIVATE_KEYS_DIR"] = str(private_keys)
            quiet(["security", "create-keychain", "-p", keychain_password, str(keychain)])
            keychain_created = True
            quiet(["security", "set-keychain-settings", "-lut", "21600", str(keychain)])
            quiet(["security", "unlock-keychain", "-p", keychain_password, str(keychain)])
            quiet(["security", "import", str(certificate), "-k", str(keychain), "-P", os.environ["APPLE_DISTRIBUTION_PASSWORD"], "-T", "/usr/bin/codesign", "-T", "/usr/bin/security"])
            quiet(["security", "set-key-partition-list", "-S", "apple-tool:,apple:", "-k", keychain_password, str(keychain)])
            quiet(["security", "list-keychains", "-d", "user", "-s", str(keychain)] + original_paths)
            profile_map = {}
            for label, bundle in BUNDLES.items():
                path = secret_file(temporary / (label + ".mobileprovision"), base64.b64decode(os.environ["APPLE_" + label.upper() + "_PROFILE_BASE64"], validate=True))
                profile = decode_profile(path, bundle)
                destination = Path.home() / "Library/Developer/Xcode/UserData/Provisioning Profiles" / (profile["UUID"] + ".mobileprovision")
                destination.parent.mkdir(parents=True, exist_ok=True)
                assert not destination.exists(), "Refuse to overwrite an existing runner profile"
                shutil.copyfile(path, destination)
                os.chmod(destination, 0o600)
                installed_profiles.append(destination)
                profile_map[bundle] = profile["UUID"]
                target = "Galleonaire" if label == "Phone" else "GalleonaireWatch"
                specification["targets"][target]["settings"]["base"].update({"CODE_SIGN_STYLE": "Manual", "CODE_SIGN_IDENTITY": "Apple Distribution", "PROVISIONING_PROFILE_SPECIFIER": profile["UUID"], "OTHER_CODE_SIGN_FLAGS": "--keychain " + str(keychain)})
            specification["settings"]["base"]["CURRENT_PROJECT_VERSION"] = build
            signing_spec.write_text(json.dumps(specification))
            run("generate-signed-project", ["xcodegen", "generate", "--spec", str(signing_spec), "--project", "Apple"])
            archive = ARTIFACTS / "Galleonaire.xcarchive"
            run("signed-archive", ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "-scheme", "Galleonaire", "-configuration", "Release", "-destination", "generic/platform=iOS", "-archivePath", str(archive), "archive"])
            verify_archive(archive, signed=True)
            quiet(["codesign", "--verify", "--deep", "--strict", str(archive / "Products/Applications/Galleonaire.app")])
            export_options = temporary / "ExportOptions.plist"
            export_options.write_bytes(plistlib.dumps({"method": "app-store-connect", "destination": "export", "teamID": TEAM, "signingStyle": "manual", "signingCertificate": "Apple Distribution", "provisioningProfiles": profile_map, "manageAppVersionAndBuildNumber": False}))
            export = ARTIFACTS / "TestFlight"
            run("export-testflight", ["xcodebuild", "-exportArchive", "-archivePath", str(archive), "-exportPath", str(export), "-exportOptionsPlist", str(export_options)])
            ipas = list(export.glob("*.ipa"))
            assert len(ipas) == 1
            report = inspect_ipa(ipas[0], build, temporary, version)
            if upload:
                run("upload-testflight", ["xcrun", "altool", "--upload-app", "--type", "ios", "--file", str(ipas[0]), "--apiKey", key_id, "--apiIssuer", os.environ["APP_STORE_CONNECT_ISSUER_ID"]])
                report["uploaded"] = True
                (ARTIFACTS / "signed-package-verification.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report, indent=2), flush=True)
        finally:
            signing_spec.unlink(missing_ok=True)
            for path in installed_profiles: path.unlink(missing_ok=True)
            if keychain_created:
                try:
                    quiet(["security", "list-keychains", "-d", "user", "-s"] + original_paths)
                finally:
                    subprocess.run(["security", "delete-keychain", str(keychain)], capture_output=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", required=True)
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    release(args.build, args.upload)
