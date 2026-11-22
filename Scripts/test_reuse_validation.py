from datetime import datetime, timezone
import unittest
from unittest.mock import patch
import reuse_validation as reuse
from reuse_validation import eligible, reviewed_test_changes, parse_model_report, baseline_run


class ReuseValidationTests(unittest.TestCase):
    def test_stage_override_keeps_other_verified_baselines(self):
        request = {"reuseValidationRun": 37, "reuseValidationRuns": {"watch": 40}}
        self.assertEqual(baseline_run(request, "watch"), 40)
        self.assertEqual(baseline_run(request, "phone-models"), 37)
        self.assertIsNone(baseline_run({}, "watch"))

    def eligible(self, state="success", tree="same", created="2026-11-07T01:00:00Z", branch="main", jobs=None):
        run = {"path": ".github/workflows/testflight.yml", "head_branch": branch, "created_at": created}
        job = {"name": "validation (phone-models, 2, 4)", "status": "completed", "conclusion": state}
        return eligible(run, [job] if jobs is None else jobs, "phone-models", 2, 4, "same", tree,
                        datetime(2026, 11, 7, 3, tzinfo=timezone.utc))

    def test_same_product_success_is_reusable(self):
        self.assertIsNotNone(self.eligible())

    def test_failure_cancellation_or_changed_product_is_never_reused(self):
        for state in ["failure", "cancelled", None]:
            self.assertIsNone(self.eligible(state=state))
        self.assertIsNone(self.eligible(tree="changed"))

    def test_old_future_or_other_branch_evidence_is_rejected(self):
        for created in ["2026-11-05T01:00:00Z", "2026-11-08T01:00:00Z"]:
            self.assertIsNone(self.eligible(created=created))
        self.assertIsNone(self.eligible(branch="other"))

    def test_missing_wrong_or_duplicate_model_group_is_rejected(self):
        job = {"name": "validation (phone-models, 1, 4)", "status": "completed", "conclusion": "success"}
        self.assertIsNone(self.eligible(jobs=[]))
        self.assertIsNone(self.eligible(jobs=[job]))
        job["name"] = "validation (phone-models, 2, 4)"
        self.assertIsNone(self.eligible(jobs=[job, job]))

    def test_only_exact_reviewed_test_locator_correction_can_differ(self):
        path = "Apple/UITests/GalleonaireUITests.swift"
        correction = [{"path": path, "baselineBlob": "old", "currentBlob": "new"}]
        self.assertTrue(reviewed_test_changes({path: ("old", "new")}, correction))
        self.assertFalse(reviewed_test_changes({path: ("old", "different")}, correction))
        self.assertFalse(reviewed_test_changes({path: ("old", "new")}, []))

    def test_app_change_cannot_be_disguised_as_test_correction(self):
        path = "Apple/App/AppRootView.swift"
        self.assertFalse(reviewed_test_changes({path: ("old", "new")},
            [{"path": path, "baselineBlob": "old", "currentBlob": "new"}]))

    def test_partial_report_keeps_failed_model_failed(self):
        log = '2026-11-07T01:00:00.000Z {\n2026-11-07T01:00:00.001Z   "platform": "iOS",\n2026-11-07T01:00:00.002Z   "models": [{"passed": true}, {"passed": false}], "complete": false\n2026-11-07T01:00:00.003Z }\ntrailing log'
        report = parse_model_report('\x1b[32m' + log + '\x1b[0m')
        self.assertFalse(report["complete"])
        self.assertEqual([m["passed"] for m in report["models"]], [True, False])
        with self.assertRaises(ValueError): parse_model_report("No result was printed")

    def test_core_reuse_rejects_changed_resources_or_test_harness(self):
        now = datetime.now(timezone.utc).isoformat()
        run = {"path": ".github/workflows/testflight.yml", "head_branch": "main",
               "created_at": now, "head_sha": "baseline"}
        job = {"id": 1, "html_url": "https://example.invalid/job", "name": "validation (unit, 0, 1)",
               "status": "completed", "conclusion": "success"}
        for changed in [False, True]:
            def fake_git(*args):
                if args[0] == "ls-tree":
                    self.assertIn("Apple/Sources", args)
                    self.assertIn("Apple/Tests", args)
                    self.assertIn("Scripts/ci.py", args)
                    self.assertIn(".github/workflows/testflight.yml", args)
                    self.assertNotIn("Apple/App", args)
                    return "changed" if changed and args[1] == "HEAD" else "same-core"
                if args[0] == "diff" and changed: return "Apple/Sources/GalleonaireCore/Resources/exam-bank.json"
                return ""
            with patch.object(reuse, "git", side_effect=fake_git), \
                 patch.object(reuse, "api", side_effect=[run, {"jobs": [job]}]), \
                 patch.object(reuse, "baseline_run", return_value=43):
                result = reuse.baseline_context("unit", 0, 1)
                self.assertEqual(bool(result), not changed)
