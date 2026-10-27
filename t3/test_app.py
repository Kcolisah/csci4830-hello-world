import tempfile
import unittest
from pathlib import Path

from app import app, init_db


class MaintenanceAppTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        app.config["TESTING"] = True
        app.config["DATABASE"] = str(Path(self.tempdir.name) / "test.sqlite3")
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_home_and_health(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["records"], 0)

    def test_submit_saves_record_to_sqlite(self):
        response = self.client.post("/add", data={
            "service": "Chain clean", "mileage": "3000", "service_date": "2026-10-27", "notes": "Test"
        })
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get("/health").json["records"], 1)
        self.assertIn(b"Chain clean", self.client.get("/").data)

    def test_bad_mileage_does_not_save(self):
        response = self.client.post("/add", data={
            "service": "Chain clean", "mileage": "-1", "service_date": "2026-10-27"
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/health").json["records"], 0)

    def test_script_input_is_escaped(self):
        self.client.post("/add", data={
            "service": "<script>alert(1)</script>", "mileage": "50", "service_date": "2026-10-27"
        })
        page = self.client.get("/").data
        self.assertNotIn(b"<script>", page)
        self.assertIn(b"&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
