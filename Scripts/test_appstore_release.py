"""Guard public submission identity and truthful completion evidence."""
import copy
import json
import unittest
from pathlib import Path
from submit_appstore import validate_metadata, verify_submission


class PublicReleaseTests(unittest.TestCase):
    def test_public_metadata_requires_explicit_matching_channel_and_version(self):
        root = Path(__file__).resolve().parents[1]
        metadata = json.loads((root / 'Docs/AppStore-Metadata.json').read_text(encoding='utf-8'))
        request = json.loads((root / 'Docs/Release-Request.json').read_text())
        validate_metadata(metadata, request)
        for replacement in [{'channel': 'testflight'}, {'version': '0.1.0'}]:
            with self.assertRaises(ValueError):
                validate_metadata(metadata, {**request, **replacement})

    def fixture(self):
        return {
            'appStoreVersions/version': {'data': {'attributes': {'versionString': '1.0.0', 'appStoreState': 'WAITING_FOR_REVIEW'}}},
            'appStoreVersions/version/build': {'data': {'id': 'verified-build'}},
            'reviewSubmissions/review': {'data': {'attributes': {'state': 'WAITING_FOR_REVIEW'}}},
            'reviewSubmissions/review/items?include=appStoreVersion&limit=200': {'data': [{'relationships': {'appStoreVersion': {'data': {'id': 'version'}}}}]},
        }

    def verify(self, responses):
        class ReadOnlyApple:
            def request(self, method, path):
                assert method == 'GET'
                return responses[path]
        return verify_submission(ReadOnlyApple(), 'version', 'verified-build', '1.0.0', 'review')

    def test_only_matching_submitted_build_can_be_reported_complete(self):
        original = self.fixture()
        self.assertTrue(self.verify(original)['submittedForPublicReview'])
        for change in ['build', 'version', 'items', 'draft']:
            values = copy.deepcopy(original)
            if change == 'build': values['appStoreVersions/version/build']['data']['id'] = 'old-build'
            if change == 'version': values['appStoreVersions/version']['data']['attributes']['versionString'] = '0.1.0'
            if change == 'items': values['reviewSubmissions/review/items?include=appStoreVersion&limit=200']['data'] = []
            if change == 'draft': values['reviewSubmissions/review']['data']['attributes']['state'] = 'READY_FOR_REVIEW'
            with self.subTest(change=change), self.assertRaises(ValueError): self.verify(values)


if __name__ == '__main__': unittest.main()
