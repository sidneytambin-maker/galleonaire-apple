from datetime import datetime, timezone
import unittest
from reuse_validation import eligible


class ReuseValidationTests(unittest.TestCase):
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
