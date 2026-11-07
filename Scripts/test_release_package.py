"""Synthetic package checks; these do not claim Apple signing or device testing."""
import datetime
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import release


class PackageValidationTests(unittest.TestCase):
    def profile(self, bundle):
        return {"TeamIdentifier": [release.TEAM], "Entitlements": {"application-identifier": release.TEAM + "." + bundle, "get-task-allow": False}, "ExpirationDate": datetime.datetime.now() + datetime.timedelta(days=30)}

    def test_only_distribution_profile_for_correct_app_is_accepted(self):
        bundle = release.BUNDLES["Watch"]
        with patch.object(release, "quiet", return_value=plistlib.dumps(self.profile(bundle))):
            self.assertEqual(release.decode_profile(Path("fixture"), bundle)["TeamIdentifier"], [release.TEAM])

    def test_development_profile_is_rejected(self):
        profile = self.profile(release.BUNDLES["Phone"])
        profile["Entitlements"]["get-task-allow"] = True
        with patch.object(release, "quiet", return_value=plistlib.dumps(profile)):
            with self.assertRaises(AssertionError): release.decode_profile(Path("fixture"), release.BUNDLES["Phone"])

    def test_profile_from_another_app_is_rejected(self):
        with patch.object(release, "quiet", return_value=plistlib.dumps(self.profile("com.example.anotherapp"))):
            with self.assertRaises(AssertionError): release.decode_profile(Path("fixture"), release.BUNDLES["Watch"])

    def test_expired_profile_is_rejected(self):
        profile = self.profile(release.BUNDLES["Phone"])
        profile["ExpirationDate"] = datetime.datetime.now() - datetime.timedelta(days=1)
        with patch.object(release, "quiet", return_value=plistlib.dumps(profile)):
            with self.assertRaises(AssertionError): release.decode_profile(Path("fixture"), release.BUNDLES["Phone"])

    def package(self, path, watch_bundle=None, watch_build="1", include_watch=True, extra_secret=False, missing_resource=None, stale_resource=None, phone_version="0.2.0", watch_version="0.2.0"):
        phone = "Payload/Galleonaire.app/"
        with zipfile.ZipFile(path, "w") as archive:
            apps = [(phone, release.BUNDLES["Phone"], "1")]
            if include_watch: apps.append((phone + "Watch/GalleonaireWatch.app/", watch_bundle or release.BUNDLES["Watch"], watch_build))
            for prefix, bundle, build in apps:
                info = {"CFBundleIdentifier": bundle, "CFBundleDisplayName": "Galleonaire", "CFBundleVersion": build, "CFBundleShortVersionString": phone_version if prefix == phone else watch_version, "WKApplication": True, "WKCompanionAppBundleIdentifier": release.BUNDLES["Phone"]}
                archive.writestr(prefix + "Info.plist", plistlib.dumps(info))
                for name in ["Assets.car", "PrivacyInfo.xcprivacy", "_CodeSignature/CodeResources", "questions.json", "exam-bank.json", "embedded.mobileprovision"] + [name + ".wav" for name in release.AUDIO]:
                    if prefix + name == missing_resource: continue
                    data = release.encoded(release.check_pack()) if name == "questions.json" else b"synthetic test fixture"
                    if name == "exam-bank.json": data = release.EXAM_BANK.read_bytes()
                    archive.writestr(prefix + name, b'{"questions": []}' if prefix + name == stale_resource else data)
            if extra_secret: archive.writestr(phone + "AuthKey_test.p8", b"not a real key")

    def verify_fixture(self, **options):
        with tempfile.TemporaryDirectory(prefix="galleonaire-package-test-") as directory:
            root = Path(directory)
            ipa = root / "fixture.ipa"
            self.package(ipa, **options)
            with patch.object(release, "ARTIFACTS", root), patch.object(release, "decode_profile"):
                return release.inspect_ipa(ipa, "1", root, "0.2.0")

    def test_valid_package_reports_not_uploaded(self):
        result = self.verify_fixture()
        self.assertTrue(result["watchEmbedded"])
        self.assertFalse(result["uploaded"])
        self.assertEqual(result["version"], "0.2.0")
        self.assertEqual(result["questionCountPerApp"], 1264)
        self.assertEqual(result["additionalQuestionCountPerApp"], 264)
        self.assertTrue(result["examBanksMatchReviewedSource"])

    def test_release_version_must_match_project_request_and_metadata(self):
        spec = {"settings": {"base": {"MARKETING_VERSION": "0.2.0"}}}
        self.assertEqual(release.configured_version(spec, {"version": "0.2.0"}, {"version": "0.2.0"}), "0.2.0")
        with self.assertRaisesRegex(AssertionError, "must agree"):
            release.configured_version(spec, {"version": "0.2.0"}, {"version": "0.1.0"})

    def test_old_version_on_either_app_is_rejected(self):
        for key in ["phone_version", "watch_version"]:
            with self.subTest(key=key), self.assertRaisesRegex(AssertionError, "configured release version"):
                self.verify_fixture(**{key: "0.1.0"})

    def test_missing_or_stale_exam_bank_on_either_app_is_rejected(self):
        for app in ["Payload/Galleonaire.app/", "Payload/Galleonaire.app/Watch/GalleonaireWatch.app/"]:
            for key in ["missing_resource", "stale_resource"]:
                with self.subTest(app=app, key=key), self.assertRaisesRegex(AssertionError, "exam bank"):
                    self.verify_fixture(**{key: app + "exam-bank.json"})

    def test_missing_watch_is_rejected(self):
        with self.assertRaises(KeyError): self.verify_fixture(include_watch=False)

    def test_wrong_watch_bundle_is_rejected(self):
        with self.assertRaises(AssertionError): self.verify_fixture(watch_bundle="com.example.wrong")

    def test_mismatched_watch_build_is_rejected(self):
        with self.assertRaises(AssertionError): self.verify_fixture(watch_build="2")

    def test_secret_in_app_package_is_rejected(self):
        with self.assertRaises(AssertionError): self.verify_fixture(extra_secret=True)

    def test_watch_questions_do_not_mask_missing_phone_questions(self):
        with self.assertRaises(AssertionError):
            self.verify_fixture(missing_resource="Payload/Galleonaire.app/questions.json")

    def test_missing_watch_sound_is_rejected(self):
        with self.assertRaises(AssertionError):
            self.verify_fixture(missing_resource="Payload/Galleonaire.app/Watch/GalleonaireWatch.app/victory.wav")

    def test_stale_question_bank_on_either_device_is_rejected(self):
        for app in ["Payload/Galleonaire.app/", "Payload/Galleonaire.app/Watch/GalleonaireWatch.app/"]:
            with self.subTest(app=app), self.assertRaisesRegex(AssertionError, "reviewed 1000-question bank"):
                self.verify_fixture(stale_resource=app + "questions.json")


if __name__ == "__main__": unittest.main()
