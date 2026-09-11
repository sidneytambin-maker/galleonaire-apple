"""Guard the personal app identity before any cloud build or release."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PersonalIdentityTests(unittest.TestCase):
    def test_release_name_has_no_added_brand(self):
        metadata = json.loads((ROOT / "Docs/TestFlight-Metadata.json").read_text())
        self.assertEqual(metadata["name"], "Galleonaire")
        project = (ROOT / "Apple/project.yml").read_text()
        self.assertEqual(project.count("CFBundleDisplayName: Galleonaire"), 2)

    def test_personal_bundle_family_is_consistent(self):
        for name in ("Apple/project.yml", "Scripts/apple_accounts.py", "Scripts/ci.py"):
            content = (ROOT / name).read_text()
            self.assertIn("com.sidneytambin.galleonaire", content, name)
            self.assertIn("com.sidneytambin.galleonaire.watchkitapp", content, name)

    def test_no_company_brand_in_shipped_app_or_release_metadata(self):
        paths = list((ROOT / "Apple/App").glob("*.swift"))
        paths += [ROOT / "Apple/project.yml", ROOT / "Docs/TestFlight-Metadata.json"]
        for path in paths:
            self.assertNotIn("inclus" + "ophy", path.read_text().lower(), str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
