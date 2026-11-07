import unittest
from compatibility import model_plan


class ModelCoverageTests(unittest.TestCase):
    def test_hardware_specific_runtime_does_not_hide_general_iphone_catalogue(self):
        duo = {"identifier": "duo", "supportedDeviceTypes": [{"name": "iPhone Duo", "identifier": "duo-phone"}]}
        general = {"identifier": "general", "supportedDeviceTypes": [
            {"name": "iPhone SE", "identifier": "small-phone"}, {"name": "iPhone Pro Max", "identifier": "large-phone"}]}
        plan = model_plan([duo, general], "iPhone")
        self.assertEqual({model["identifier"] for _, model in plan}, {"duo-phone", "small-phone", "large-phone"})

    def test_duplicate_device_types_use_the_general_runtime_once(self):
        phone = {"name": "iPhone", "identifier": "phone"}
        specialist = {"identifier": "specialist", "supportedDeviceTypes": [phone]}
        general = {"identifier": "general", "supportedDeviceTypes": [phone, {"name": "iPad", "identifier": "ipad"}]}
        plan = model_plan([specialist, general], "iPhone")
        self.assertEqual([(r["identifier"], d["identifier"]) for r, d in plan], [("general", "phone")])

    def test_empty_platform_coverage_fails_instead_of_reporting_success(self):
        with self.assertRaises(RuntimeError):
            model_plan([{"supportedDeviceTypes": [{"name": "iPhone", "identifier": "phone"}]}], "Apple Watch")
