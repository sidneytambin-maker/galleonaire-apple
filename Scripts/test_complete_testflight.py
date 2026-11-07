import unittest
from unittest.mock import Mock

from complete_testflight import configure_review_and_notifications


class CompletionSettingsTests(unittest.TestCase):
    notes = "Exam Mode works offline without an account, alongside Classic."

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
