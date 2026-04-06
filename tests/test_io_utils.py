import csv
from pathlib import Path
import tempfile
import unittest

from scholarship_pipeline.io_utils import save_output, save_to_csv


class SaveCsvTests(unittest.TestCase):
    def test_save_to_csv_writes_expected_rows(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "results.csv"
            rows = [
                {
                    "source_file": "bundle_5_page.pdf",
                    "source_page": 1,
                    "name": "Alice Example",
                    "needs_review": False,
                },
                {
                    "source_file": "bundle_5_page.pdf",
                    "source_page": 2,
                    "name": "Bob Example",
                    "needs_review": True,
                },
            ]

            save_to_csv(rows, output_file=str(output_path))

            with output_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                loaded_rows = list(reader)

            self.assertEqual(len(loaded_rows), 2)
            self.assertEqual(loaded_rows[0]["source_file"], "bundle_5_page.pdf")
            self.assertEqual(loaded_rows[1]["name"], "Bob Example")

    def test_save_output_routes_csv_files_to_csv_export(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "results.csv"
            rows = [{"field": "value"}]

            save_output(rows, output_file=str(output_path))

            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
