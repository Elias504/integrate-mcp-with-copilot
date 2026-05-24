import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException


class ActivityQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "activities.sqlite")

        cls.app_module = importlib.import_module("src.app")
        cls.app_module = importlib.reload(cls.app_module)
        cls.app_module.initialize_database()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
        os.environ.pop("DATABASE_PATH", None)

    def test_search_matches_name(self):
        activities = self.app_module.fetch_all_activities(search="soccer")
        self.assertEqual(list(activities.keys()), ["Soccer Team"])

    def test_search_matches_description(self):
        activities = self.app_module.fetch_all_activities(search="creativity")
        self.assertEqual(list(activities.keys()), ["Art Club"])

    def test_schedule_filter_returns_matching_activities(self):
        activities = self.app_module.fetch_all_activities(schedule="Fridays")
        self.assertEqual(
            list(activities.keys()),
            ["Basketball Team", "Chess Club", "Debate Team", "Gym Class"],
        )

    def test_sort_by_availability_desc(self):
        activities = self.app_module.fetch_all_activities(sort="availability_desc")
        self.assertEqual(next(iter(activities)), "Gym Class")

    def test_get_activities_rejects_invalid_sort(self):
        with self.assertRaises(HTTPException) as context:
            self.app_module.get_activities(sort="invalid_sort")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            "Invalid sort value. Supported values: name_asc, name_desc, availability_desc",
        )


if __name__ == "__main__":
    unittest.main()
