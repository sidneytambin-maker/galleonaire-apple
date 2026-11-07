import unittest
from compatibility import model_plan, assigned_models


class ModelCoverageTests(unittest.TestCase):
    def test_shards_cover_every_model_exactly_once(self):
        models = list(range(34))
        shards = [assigned_models(models, index, 4) for index in range(4)]
        self.assertEqual(sorted(model for shard in shards for model in shard), models)
        self.assertEqual([len(shard) for shard in shards], [9, 9, 8, 8])

    def test_invalid_or_empty_shards_are_rejected(self):
        for index, count in [(-1, 4), (4, 4), (0, 0), (0, 35)]:
            with self.assertRaises(ValueError): assigned_models(list(range(34)), index, count)

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
