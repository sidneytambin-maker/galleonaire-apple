import unittest
from unittest.mock import Mock, patch

from complete_testflight import configure_review_and_notifications, availability_snapshot, pending_review_outcome


class CompletionSettingsTests(unittest.TestCase):
    notes = "Exam Mode works offline without an account, alongside Classic."

    def test_ordinary_review_wait_remains_pending_without_a_workflow_error(self):
        result = {"availableForTesting": False, "betaReviewState": "WAITING_FOR_REVIEW",
                  "externalBuildState": "WAITING_FOR_BETA_REVIEW", "buildNumber": "42"}
        pending = pending_review_outcome(result)
        self.assertFalse(pending["availableForTesting"])
        self.assertEqual(pending["monitoringState"], "AWAITING_APPLE_REVIEW")
        self.assertEqual(pending["buildNumber"], "42")
        self.assertNotIn("monitoringState", result)

    def test_rejection_and_unknown_states_are_not_silenced_as_pending(self):
        for review, external in [("REJECTED", "BETA_REJECTED"),
                                 ("APPROVED", "EXPIRED"), (None, None),
                                 ("WAITING_FOR_REVIEW", "FAILED")]:
            with self.subTest(review=review, external=external):
                with self.assertRaises(TimeoutError):
                    pending_review_outcome({"availableForTesting": False,
                        "betaReviewState": review, "externalBuildState": external})

    def test_conflicting_success_flag_cannot_be_treated_as_pending(self):
        with self.assertRaises(TimeoutError):
            pending_review_outcome({"availableForTesting": True,
                "betaReviewState": "WAITING_FOR_REVIEW", "externalBuildState": "WAITING_FOR_BETA_REVIEW"})

    def client(self, saved_notes=None, enabled=True):
        apple = Mock()
        apple.request.side_effect = [
            {"data": {"id": "review", "attributes": {"contactEmail": "private@example.invalid"}}}, {},
            {"data": {"attributes": {"notes": self.notes if saved_notes is None else saved_notes}}},
            {"data": {"id": "detail"}}, {}, {"data": {"attributes": {"autoNotifyEnabled": enabled}}}]
        return apple

    def test_updates_notes_and_distribution_without_overwriting_contact(self):
        apple = self.client()
        configure_review_and_notifications(apple, "app", "build", self.notes)
        updates = [call.args for call in apple.request.call_args_list if call.args[0] == "PATCH"]
        self.assertEqual(updates[0][2]["data"]["attributes"], {"notes": self.notes})
        self.assertEqual(updates[1][2]["data"]["attributes"], {"autoNotifyEnabled": True})
        self.assertNotIn("private@example.invalid", repr(updates))

    def test_missing_saved_notes_stop_before_enabling_distribution(self):
        apple = self.client(saved_notes="old notes")
        with self.assertRaisesRegex(ValueError, "review notes"):
            configure_review_and_notifications(apple, "app", "build", self.notes)
        self.assertFalse(any("buildBetaDetail" in call.args[1] for call in apple.request.call_args_list))

    def test_disabled_notifications_are_not_reported_successful(self):
        with self.assertRaisesRegex(ValueError, "notifications"):
            configure_review_and_notifications(self.client(enabled=False), "app", "build", self.notes)

    def test_pending_review_is_not_available_even_if_distribution_state_is_ready(self):
        apple = Mock()
        apple.request.side_effect = [
            {"data": {"attributes": {"internalBuildState": "IN_BETA_TESTING", "externalBuildState": "IN_BETA_TESTING"}}},
            {"data": [{"attributes": {"betaReviewState": "WAITING_FOR_REVIEW"}}]}]
        result = availability_snapshot(apple, "app", "build", 41, {"version": "0.2.0"})
        self.assertFalse(result["availableForTesting"])
        self.assertEqual(result["betaReviewState"], "WAITING_FOR_REVIEW")

    @patch("complete_testflight.checked_groups", return_value=["owner", "community"])
    @patch("complete_testflight.checked_build", return_value=("app", "build"))
    def test_final_availability_rechecks_exact_build_and_both_groups(self, build, groups):
        apple = Mock()
        apple.request.side_effect = [
            {"data": {"attributes": {"internalBuildState": "IN_BETA_TESTING", "externalBuildState": "IN_BETA_TESTING"}}},
            {"data": [{"attributes": {"betaReviewState": "APPROVED"}}]},
            {"data": [{"id": "build"}]}, {"data": [{"id": "build"}]}]
        result = availability_snapshot(apple, "app", "build", 41, {"version": "0.2.0"})
        self.assertTrue(result["availableForTesting"])
        self.assertEqual(result["groupIDs"], ["owner", "community"])
        build.assert_called_once_with(apple, 41, "0.2.0")

    @patch("complete_testflight.checked_groups", return_value=["owner", "community"])
    @patch("complete_testflight.checked_build", return_value=("app", "build"))
    def test_missing_final_group_assignment_prevents_completion(self, build, groups):
        apple = Mock()
        apple.request.side_effect = [
            {"data": {"attributes": {"internalBuildState": "IN_BETA_TESTING", "externalBuildState": "IN_BETA_TESTING"}}},
            {"data": [{"attributes": {"betaReviewState": "APPROVED"}}]},
            {"data": [{"id": "build"}]}, {"data": []}]
        with self.assertRaisesRegex(ValueError, "testing group"):
            availability_snapshot(apple, "app", "build", 41, {"version": "0.2.0"})
