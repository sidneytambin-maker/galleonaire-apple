import datetime
import hashlib
import unittest

from direct_upload import checked_operations, chunk_matches, commit_payload, file_payload, upload_payload
from local_sign import check_profile, distribution_entitlements, TEAM
from local_beta import checked_upload


class LocalReleaseTests(unittest.TestCase):
    def profile(self):
        return {"TeamIdentifier": [TEAM], "ExpirationDate": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
            "DeveloperCertificates": [b"certificate"], "Entitlements": {"application-identifier": TEAM + ".com.sidneytambin.galleonaire",
            "com.apple.developer.team-identifier": TEAM, "get-task-allow": False, "beta-reports-active": True}}

    def check(self, profile):
        return check_profile(profile, "com.sidneytambin.galleonaire", b"certificate")

    def test_matching_app_store_profile(self):
        self.assertFalse(self.check(self.profile())["get-task-allow"])

    def test_only_app_entitlements_are_signed_not_profile_wildcards(self):
        result = distribution_entitlements("com.sidneytambin.galleonaire.watchkitapp")
        self.assertEqual(result["application-identifier"], TEAM + ".com.sidneytambin.galleonaire.watchkitapp")
        self.assertEqual(len(result), 4)
        self.assertNotIn("keychain-access-groups", result)
        with self.assertRaises(AssertionError): distribution_entitlements("another.app")

    def test_publication_requires_exact_apple_processed_upload(self):
        receipt = {"app": "6811170867", "sha256": "hash", "build": "13", "uploaded": True,
                   "allPartChecksumsVerified": True, "uploadId": "upload"}
        signing = {"ipaSHA256": "hash", "build": "13", "signatureInspectionComplete": True}
        upload = {"uploadId": "upload", "build": "13", "state": {"state": "COMPLETE", "errors": []},
                  "buildResource": {"type": "builds", "id": "build"}}
        checked_upload(receipt, signing, upload, "build")
        for state in ("PROCESSING", "FAILED", "AWAITING_UPLOAD"):
            with self.assertRaises(AssertionError):
                checked_upload(receipt, signing, {**upload, "state": {"state": state}}, "build")
        with self.assertRaises(AssertionError): checked_upload(receipt, signing, upload, "other-build")
        with self.assertRaises(AssertionError): checked_upload({**receipt, "sha256": "changed"}, signing, upload, "build")
        with self.assertRaises(AssertionError): checked_upload({**receipt, "app": "other-app"}, signing, upload, "build")
        with self.assertRaises(AssertionError): checked_upload({**receipt, "uploaded": False}, signing, upload, "build")

    def test_wrong_bundle_team_or_certificate_rejected(self):
        for kind in ("bundle", "team", "cert"):
            p = self.profile()
            if kind == "bundle": p["Entitlements"]["application-identifier"] = TEAM + ".another.app"
            if kind == "team": p["TeamIdentifier"] = ["ANOTHER"]
            if kind == "cert": p["DeveloperCertificates"] = [b"another"]
            with self.assertRaises(AssertionError): self.check(p)

    def test_development_and_enterprise_profiles_rejected(self):
        for key, value in [("ProvisionedDevices", ["device"]), ("ProvisionsAllDevices", True)]:
            p = self.profile(); p[key] = value
            with self.assertRaises(AssertionError): self.check(p)
        p = self.profile(); p["Entitlements"]["get-task-allow"] = True
        with self.assertRaises(AssertionError): self.check(p)

    def test_expired_or_non_beta_profile_rejected(self):
        p = self.profile(); p["ExpirationDate"] -= datetime.timedelta(days=31)
        with self.assertRaises(AssertionError): self.check(p)
        p = self.profile(); p["Entitlements"]["beta-reports-active"] = False
        with self.assertRaises(AssertionError): self.check(p)

    def operations(self):
        return [{"method": "PUT", "offset": 0, "length": 5, "url": "https://delivery.apple.com/part1", "requestHeaders": []},
                {"method": "PUT", "offset": 5, "length": 7, "url": "https://delivery.apple.com/part2", "requestHeaders": []}]

    def test_complete_chunks_in_any_order(self):
        self.assertEqual(checked_operations(list(reversed(self.operations())), 12), self.operations())

    def test_gaps_overlaps_or_truncation_rejected(self):
        for offset in (4, 6):
            operations = self.operations(); operations[1]["offset"] = offset
            with self.assertRaises(AssertionError): checked_operations(operations, 12)
        with self.assertRaises(AssertionError): checked_operations(self.operations(), 13)
        with self.assertRaises(AssertionError): checked_operations([], 12)

    def test_delivery_host_transport_and_headers_are_restricted(self):
        for url in ["http://delivery.apple.com/a", "https://apple.com.evil.example/a", "https://localhost/a", "https://user:password@delivery.apple.com/a"]:
            operations = self.operations(); operations[0]["url"] = url
            with self.assertRaises(AssertionError): checked_operations(operations, 12)
        operations = self.operations(); operations[0]["requestHeaders"] = [{"name": "Cookie", "value": "private"}]
        with self.assertRaises(AssertionError): checked_operations(operations, 12)

    def test_official_upload_payloads_are_exactly_scoped(self):
        upload = upload_payload("6811170867", 13)["data"]
        self.assertEqual(upload["attributes"], {"cfBundleShortVersionString": "0.1.0", "cfBundleVersion": "13", "platform": "IOS"})
        self.assertEqual(upload["relationships"]["app"]["data"]["id"], "6811170867")
        file = file_payload("upload-id", 100)["data"]
        self.assertEqual(file["attributes"]["uti"], "com.apple.ipa")
        self.assertEqual(file["relationships"]["buildUpload"]["data"]["id"], "upload-id")
        with self.assertRaises(AssertionError): file_payload("upload-id", 0)

    def test_commit_does_not_invent_optional_server_checksums(self):
        self.assertEqual(commit_payload("file-id"), {"data": {"id": "file-id", "type": "buildUploadFiles", "attributes": {"uploaded": True}}})

    def test_received_part_tags_match_exact_byte_ranges(self):
        payload = b"hello world!"
        for operation in self.operations():
            self.assertFalse(chunk_matches(operation, payload))
            start, length = operation["offset"], operation["length"]
            operation["entityTag"] = '"' + hashlib.md5(payload[start:start + length]).hexdigest().upper() + '"'
            self.assertTrue(chunk_matches(operation, payload))
            self.assertFalse(chunk_matches(operation, b"X" * len(payload)))
