import unittest
from unittest.mock import Mock, patch

import beta_release as release


class BetaReleaseTests(unittest.TestCase):
    def client(self, **attributes):
        apple = Mock()
        build = {"id": "build-3", "attributes": {"version": "3", "processingState": "VALID", "expired": False, "usesNonExemptEncryption": False, **attributes}}
        apple.request.side_effect = [
            {"data": [build]}, {"data": {"id": "galleonaire"}},
            {"data": {"attributes": {"version": "0.1.0", "platform": "IOS"}}}]
        return apple

    @patch.object(release, "resolve_app", return_value="galleonaire")
    def test_valid_exact_build(self, _):
        self.assertEqual(release.checked_build(self.client(), 3, "0.1.0"), ("galleonaire", "build-3"))

    @patch.object(release, "resolve_app", return_value="galleonaire")
    def test_processing_expired_wrong_number_or_unknown_encryption_cannot_publish(self, _):
        for change in [{"processingState": "PROCESSING"}, {"expired": True}, {"version": "2"}, {"usesNonExemptEncryption": None}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                release.checked_build(self.client(**change), 3, "0.1.0")

    @patch.object(release, "resolve_app", return_value="galleonaire")
    def test_wrong_marketing_version_rejected(self, _):
        with self.assertRaises(ValueError): release.checked_build(self.client(), 3, "1.0")

    @patch.object(release, "resolve_app", return_value="galleonaire")
    def test_another_app_build_rejected(self, _):
        apple = self.client()
        replies = list(apple.request.side_effect)
        replies[1] = {"data": {"id": "court-story"}}
        apple.request.side_effect = replies
        with self.assertRaises(ValueError): release.checked_build(apple, 3, "0.1.0")

    @patch.object(release, "checked_groups", return_value=["owner-group", "external-group"])
    @patch.object(release, "checked_build", return_value=("galleonaire", "build-3"))
    def test_notes_and_exact_build_assignments_are_read_back(self, *_):
        notes = "Test the complete game and accessible Watch controls."
        metadata = {"version": "0.1.0", "primaryLocale": "en-GB", "whatToTest": notes}
        saved = {"data": [{"attributes": {"locale": "en-GB", "whatsNew": notes}}]}
        linked = {"data": [{"type": "builds", "id": "build-3"}]}
        apple = Mock()
        apple.request.side_effect = [{"data": []}, {}, saved, {"data": []}, None, linked, {"data": []}, None, linked]
        result = release.prepare(apple, 3, metadata)
        self.assertTrue(result["groupsVerified"])
        posts = [call for call in apple.request.call_args_list if call.args[0] == "POST"]
        self.assertEqual(len(posts), 3)
        self.assertEqual(posts[0].args[2]["data"]["attributes"]["whatsNew"], notes)
        for call in posts[1:]:
            self.assertEqual(call.args[2], linked)

    @patch.object(release, "checked_groups", return_value=["owner-group", "external-group"])
    @patch.object(release, "checked_build", return_value=("galleonaire", "build-3"))
    def test_missing_saved_notes_prevent_group_assignment(self, *_):
        apple = Mock()
        apple.request.side_effect = [{"data": []}, {}, {"data": []}]
        metadata = {"version": "0.1.0", "primaryLocale": "en-GB", "whatToTest": "Test complete iPhone and Watch games."}
        with self.assertRaises(ValueError): release.prepare(apple, 3, metadata)
        self.assertFalse(any("relationships/builds" in call.args[1] for call in apple.request.call_args_list))

    @patch.object(release, "prepare", return_value={"build": "build-3"})
    def test_pending_review_is_not_resubmitted_or_called_live(self, _):
        apple = Mock()
        apple.request.return_value = {"data": [{"attributes": {"betaReviewState": "WAITING_FOR_REVIEW"}}]}
        result = release.submit(apple, 3, {})
        self.assertEqual(result["betaReviewState"], "WAITING_FOR_REVIEW")
        self.assertFalse(result["publicLinkEnabledByThisAction"])
        apple.request.assert_called_once()

    @patch.object(release, "prepare", return_value={"build": "build-3"})
    def test_rejected_review_is_not_silently_resubmitted(self, _):
        apple = Mock()
        apple.request.return_value = {"data": [{"attributes": {"betaReviewState": "REJECTED"}}]}
        with self.assertRaises(ValueError): release.submit(apple, 3, {})
        apple.request.assert_called_once()

    @patch.object(release, "prepare", return_value={"build": "build-3"})
    def test_new_submission_is_verified_before_reporting(self, _):
        apple = Mock()
        apple.request.side_effect = [{"data": []}, {"data": {}}, {"data": [{"attributes": {"betaReviewState": "IN_REVIEW"}}]}]
        result = release.submit(apple, 3, {})
        self.assertEqual(result["betaReviewState"], "IN_REVIEW")
        self.assertEqual(apple.request.call_args_list[1].args[1], "betaAppReviewSubmissions")


if __name__ == "__main__": unittest.main()
