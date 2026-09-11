import json
import unittest
from unittest.mock import Mock

import beta_metadata as beta


class BetaMetadataTests(unittest.TestCase):
    def test_another_app_is_never_accepted(self):
        apple = Mock()
        apple.request.return_value = {"data": [{"id": "wrong", "attributes": {"name": "Court Story", "bundleId": "com.example.other"}}]}
        with self.assertRaises(ValueError): beta.resolve_app(apple)
        self.assertEqual(apple.request.call_args.args[0], "GET")

    def test_missing_app_fails_without_creating_an_unrelated_record(self):
        apple = Mock()
        apple.request.return_value = {"data": []}
        with self.assertRaises(ValueError): beta.resolve_app(apple)
        apple.request.assert_called_once()

    def test_exact_personal_app_is_accepted(self):
        apple = Mock()
        apple.request.return_value = {"data": [{"id": "galleonaire", "attributes": {"name": "Galleonaire", "bundleId": beta.BUNDLES["Phone"]}}]}
        self.assertEqual(beta.resolve_app(apple), "galleonaire")

    def test_missing_contact_is_not_invented(self):
        metadata = json.loads((beta.ROOT / "Docs/TestFlight-Metadata.json").read_text())
        with self.assertRaises(ValueError): beta.review_fields(metadata, {})

    def test_review_notes_do_not_claim_account_or_real_money_features(self):
        metadata = json.loads((beta.ROOT / "Docs/TestFlight-Metadata.json").read_text())
        fields = beta.review_fields(metadata, {"contactPhone": "+44 7700 900000"})
        self.assertFalse(fields["demoAccountRequired"])
        self.assertIn("fictional", fields["notes"])


if __name__ == "__main__": unittest.main()
