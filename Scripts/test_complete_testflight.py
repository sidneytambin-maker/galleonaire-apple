import unittest
from unittest.mock import Mock, patch

import complete_testflight as completion


class ProcessingGateTests(unittest.TestCase):
    @patch.object(completion.time, "sleep")
    @patch.object(completion, "checked_build")
    def test_processing_retries_then_returns_the_exact_checked_build(self, checked, sleep):
        checked.side_effect = [ValueError("The exact release build is still processing"), ("app", "build")]
        self.assertEqual(completion.wait_for_build(Mock(), 20, "0.1.0", float("inf")), ("app", "build"))
        sleep.assert_called_once_with(60)

    @patch.object(completion.time, "sleep")
    @patch.object(completion, "checked_build")
    def test_invalid_build_identity_or_encryption_is_never_retried(self, checked, sleep):
        for message in ["The release build is not valid and unexpired", "The build belongs to a different app, version or platform", "Apple has not confirmed the build's export compliance declaration"]:
            checked.side_effect = ValueError(message)
            with self.assertRaisesRegex(ValueError, message):
                completion.wait_for_build(Mock(), 20, "0.1.0", float("inf"))
        sleep.assert_not_called()
