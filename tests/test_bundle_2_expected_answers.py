import csv
import os
import unittest
from pathlib import Path

from scholarship_pipeline.config import configure_binaries
from scholarship_pipeline.io_utils import pdf_to_images
from scholarship_pipeline.pipeline import process_document
from scholarship_pipeline.postprocess import finalize_record, merge_page_records


def _load_run_settings(path):
    settings = {}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (row.get("key") or "").strip()
            value = (row.get("value") or "").strip()
            if key:
                settings[key] = value

    return settings


def _load_expected_answers(path):
    expected = {}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, skipinitialspace=True)
        _ = next(reader, None)

        for row in reader:
            if not row:
                continue

            field = row[0].strip() if len(row) > 0 else ""
            value = row[1].strip() if len(row) > 1 else ""

            if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                value = value[1:-1]

            if not field:
                continue

            # Allow partially filled expected files by skipping blank expected values.
            if value == "":
                continue

            expected[field] = value

    return expected


def _normalize(value):
    if value is None:
        return ""

    normalized = str(value).strip()

    # Allow quoted CSV text fields to match raw OCR text fields.
    if normalized.startswith('"') and normalized.endswith('"') and len(normalized) >= 2:
        normalized = normalized[1:-1].strip()

    # Normalize line breaks and duplicate spaces for stable comparisons.
    normalized = " ".join(normalized.replace("\r", " ").replace("\n", " ").split())
    return normalized


class Bundle2ExpectedAnswersTests(unittest.TestCase):
    def test_bundle_2_pdf_matches_expected_answers(self):
        repo_root = Path(__file__).resolve().parents[1]
        bundle_root = repo_root / "test_inputs" / "applicant_bundle_2_page"
        run_settings_path = bundle_root / "run_settings.csv"

        self.assertTrue(run_settings_path.exists(), f"Missing run settings: {run_settings_path}")

        settings = _load_run_settings(run_settings_path)

        pdf_path = bundle_root / settings["input_pdf_relpath"]
        expected_path = bundle_root / settings["expected_answers_relpath"]

        self.assertTrue(pdf_path.exists(), f"Missing PDF input for bundle test: {pdf_path}")
        self.assertTrue(expected_path.exists(), f"Missing expected answers file: {expected_path}")

        expected = _load_expected_answers(expected_path)
        self.assertGreater(len(expected), 0, "No expected values found in expected_answers.csv")

        configure_binaries()

        image_paths = pdf_to_images(str(pdf_path))
        page_records = []

        try:
            for page_number, image_path in enumerate(image_paths, start=1):
                extracted = process_document(image_path, page_number=page_number)
                page_records.append(
                    finalize_record(
                        extracted,
                        source_file=pdf_path.name,
                        source_page=page_number,
                    )
                )
        finally:
            for image_path in image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)

        merged = merge_page_records(page_records)

        mismatches = []
        missing_keys = []

        for field, expected_value in expected.items():
            if field not in merged:
                missing_keys.append(field)
                continue

            expected_value_normalized = _normalize(expected_value)
            actual_value = _normalize(merged.get(field))
            if actual_value != expected_value_normalized:
                mismatches.append((field, expected_value, actual_value))

        details = []
        if missing_keys:
            details.append("Missing fields: " + ", ".join(missing_keys))

        if mismatches:
            preview = [
                f"{field}: expected='{exp}' actual='{act}'"
                for field, exp, act in mismatches[:20]
            ]
            details.append("Mismatches:\n" + "\n".join(preview))

        if details:
            self.fail("\n\n".join(details))


if __name__ == "__main__":
    unittest.main()
