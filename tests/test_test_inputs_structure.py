from pathlib import Path
import csv
import unittest


class TestInputStructureTests(unittest.TestCase):
    def test_initial_bundle_directories_exist(self):
        root = Path(__file__).resolve().parents[1] / "test_inputs"

        expected_paths = [
            root / "applicant_bundle_5_page",
            root / "applicant_bundle_5_page" / "applications" / "scholarship_form",
            root / "applicant_bundle_5_page" / "applications" / "declaration_form",
            root / "applicant_bundle_5_page" / "applications" / "travel_scholarship_form",
            root / "applicant_bundle_5_page" / "applications" / "travel_scholarship_form" / "travel_reason_form",
            root / "applicant_bundle_5_page" / "applications" / "watched_scholarship_form",
            root / "applicant_bundle_5_page" / "applications" / "watched_form",
            root / "applicant_bundle_5_page" / "applications" / "gss_scholarship_form",
            root / "applicant_bundle_5_page" / "applications" / "scholarship_gss_form",
            root / "applicant_bundle_5_page" / "applications" / "watched_scholarship_gss_form",
            root / "applicant_bundle_5_page" / "shared_attachments" / "university_grades",
            root / "applicant_bundle_5_page" / "shared_attachments" / "residency",
            root / "applicant_bundle_5_page" / "shared_attachments" / "self_economic_declaration",
            root / "applicant_bundle_5_page" / "shared_attachments" / "nation_membership",
            root / "applicant_bundle_2_page",
            root / "applicant_bundle_2_page" / "applications" / "scholarship_form",
            root / "applicant_bundle_2_page" / "applications" / "declaration_form",
            root / "applicant_bundle_2_page" / "applications" / "travel_scholarship_form",
            root / "applicant_bundle_2_page" / "applications" / "travel_scholarship_form" / "travel_reason_form",
            root / "applicant_bundle_2_page" / "applications" / "watched_form",
            root / "applicant_bundle_2_page" / "applications" / "scholarship_gss_form",
            root / "applicant_bundle_2_page" / "applications" / "watched_scholarship_gss_form",
            root / "applicant_bundle_2_page" / "shared_attachments" / "university_grades",
            root / "applicant_bundle_2_page" / "shared_attachments" / "residency",
            root / "applicant_bundle_2_page" / "shared_attachments" / "self_economic_declaration",
            root / "applicant_bundle_2_page" / "shared_attachments" / "nation_membership",
        ]

        for path in expected_paths:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"Missing expected test input path: {path}")
                self.assertTrue(path.is_dir(), f"Expected directory, found file: {path}")

    def test_bundle_csv_files_exist(self):
        root = Path(__file__).resolve().parents[1] / "test_inputs"

        expected_files = [
            root / "bundles.csv",
            root / "applicant_bundle_5_page" / "manifest.csv",
            root / "applicant_bundle_5_page" / "shared_attachments" / "README.md",
            root / "applicant_bundle_5_page" / "optional_attachments" / "README.md",
            root / "applicant_bundle_2_page" / "manifest.csv",
            root / "applicant_bundle_2_page" / "run_settings.csv",
            root / "applicant_bundle_2_page" / "applications" / "scholarship_form" / "README.md",
            root / "applicant_bundle_2_page" / "expected" / "README.md",
            root / "applicant_bundle_2_page" / "expected" / "expected_answers.csv",
        ]

        for path in expected_files:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"Missing expected file: {path}")
                self.assertTrue(path.is_file(), f"Expected file, found directory: {path}")

    def test_optional_attachment_directories_exist_for_five_page_bundle(self):
        root = Path(__file__).resolve().parents[1] / "test_inputs" / "applicant_bundle_5_page"

        optional_paths = [
            root / "optional_attachments" / "highschool_grades",
            root / "optional_attachments" / "nation_registration_confirmation",
        ]

        for path in optional_paths:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), f"Missing optional test input path: {path}")
                self.assertTrue(path.is_dir(), f"Expected directory, found file: {path}")

    def test_bundle_index_csv_is_parseable(self):
        root = Path(__file__).resolve().parents[1] / "test_inputs"
        bundle_index = root / "bundles.csv"

        with bundle_index.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["bundle_id"], "applicant_bundle_5_page")
        self.assertEqual(rows[1]["expected_page_grouping"], "2 pages")


if __name__ == "__main__":
    unittest.main()
