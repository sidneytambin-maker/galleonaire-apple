import copy
import json
from pathlib import Path
import tempfile
import unittest

from record_testflight_availability import record_availability


class AvailabilityRecordTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.evidence = root / "evidence.json"
        self.status = root / "status.md"
        self.evidence.write_text(json.dumps({
            "release": {"version": "0.2.0", "build": "42", "workflowRun": 123, "commit": "signed"},
            "appleAvailability": {"app": "app", "build": "build-id", "groups": [
                {"id": "owner", "name": "Owner Testing"}, {"id": "community", "name": "Community Beta"}]},
            "validation": {"retained": True}}))
        self.status.write_text("# Release 42: 7 November 2026\n\nPending.\n\nExam Mode provides all ten subjects\nHistorical record retained.\n")
        self.run = {"id": 123, "head_sha": "signed", "run_number": 42}
        self.snapshot = {
            "availableForTesting": True, "version": "0.2.0", "buildNumber": "42",
            "app": "app", "build": "build-id", "processingState": "VALID",
            "betaReviewState": "APPROVED", "internalBuildState": "IN_BETA_TESTING",
            "externalBuildState": "IN_BETA_TESTING", "groupsVerified": True,
            "groupIDs": ["owner", "community"], "verifiedAt": "2026-11-07T12:00:00+00:00"}

    def assert_rejected_without_changes(self, snapshot=None, run=None):
        before = (self.evidence.read_bytes(), self.status.read_bytes())
        with self.assertRaises(ValueError):
            record_availability(self.evidence, self.status, snapshot or self.snapshot, run or self.run)
        self.assertEqual(before, (self.evidence.read_bytes(), self.status.read_bytes()))

    def test_pending_review_never_records_completion(self):
        self.snapshot.update(availableForTesting=False, betaReviewState="WAITING_FOR_REVIEW")
        before = (self.evidence.read_bytes(), self.status.read_bytes())
        self.assertFalse(record_availability(self.evidence, self.status, self.snapshot, self.run))
        self.assertEqual(before, (self.evidence.read_bytes(), self.status.read_bytes()))

    def test_approved_exact_build_records_both_groups_and_preserves_history(self):
        self.assertTrue(record_availability(self.evidence, self.status, self.snapshot, self.run))
        result = json.loads(self.evidence.read_text())
        self.assertTrue(result["validation"]["retained"])
        self.assertEqual([True, True], [g["containsBuild"] for g in result["appleAvailability"]["groups"]])
        self.assertIn("Apple reports testing active for both groups", self.status.read_text())
        self.assertIn("not been directly observed", self.status.read_text())
        self.assertIn("Historical record retained.", self.status.read_text())

    def test_false_completion_flag_cannot_bypass_apple_states(self):
        for key, value in [("betaReviewState", "WAITING_FOR_REVIEW"),
                           ("externalBuildState", "WAITING_FOR_BETA_REVIEW"),
                           ("internalBuildState", "EXPIRED"), ("processingState", "PROCESSING"),
                           ("groupsVerified", False)]:
            with self.subTest(key=key):
                snapshot = copy.deepcopy(self.snapshot)
                snapshot[key] = value
                self.assert_rejected_without_changes(snapshot)

    def test_wrong_app_version_build_or_signed_run_is_rejected(self):
        for key in ["app", "build", "buildNumber", "version"]:
            with self.subTest(key=key):
                snapshot = dict(self.snapshot, **{key: "different"})
                self.assert_rejected_without_changes(snapshot)
        for key in ["id", "head_sha", "run_number"]:
            with self.subTest(key=key):
                self.assert_rejected_without_changes(run=dict(self.run, **{key: "different"}))

    def test_missing_or_different_group_is_rejected(self):
        for groups in [["owner"], ["owner", "different"]]:
            self.assert_rejected_without_changes(dict(self.snapshot, groupIDs=groups))

    def test_verification_time_and_status_release_are_required(self):
        self.assert_rejected_without_changes(dict(self.snapshot, verifiedAt="2026-11-07T12:00:00"))
        self.status.write_text("# Release 43\n\nExam Mode provides all ten subjects")
        self.assert_rejected_without_changes()


if __name__ == "__main__":
    unittest.main()
