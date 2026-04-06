import unittest
from unittest.mock import patch

import numpy as np

from scholarship_pipeline.ocr import extract_fields_regions
from scholarship_pipeline.pipeline import process_document


class OcrPageRoutingTests(unittest.TestCase):
    @patch("scholarship_pipeline.ocr.crop_with_padding", side_effect=lambda image, rel_box: image)
    @patch("scholarship_pipeline.ocr.pytesseract.image_to_string", return_value="ok")
    def test_extract_fields_uses_page_specific_mapping(self, mock_ocr, _mock_crop):
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("scholarship_pipeline.ocr.FIELDS", {"page1_field": (0.1, 0.1, 0.1, 0.1)}), patch(
            "scholarship_pipeline.ocr.FIELDS_BY_PAGE",
            {
                1: {"page1_field": (0.1, 0.1, 0.1, 0.1)},
                2: {"page2_field": (0.2, 0.2, 0.1, 0.1)},
            },
        ):
            page_1 = extract_fields_regions(image, page_number=1)
            page_2 = extract_fields_regions(image, page_number=2)

        self.assertIn("page1_field", page_1)
        self.assertNotIn("page2_field", page_1)
        self.assertIn("page2_field", page_2)
        self.assertNotIn("page1_field", page_2)
        self.assertEqual(mock_ocr.call_count, 2)

    @patch("scholarship_pipeline.pipeline.extract_data", return_value={"name": "Alice"})
    @patch("scholarship_pipeline.pipeline.preprocess_image", return_value="processed")
    def test_process_document_passes_page_number(self, mock_preprocess, mock_extract_data):
        _ = process_document("some-page.jpg", page_number=2)

        mock_preprocess.assert_called_once_with("some-page.jpg")
        mock_extract_data.assert_called_once_with("processed", page_number=2)

    @patch("scholarship_pipeline.ocr.crop_with_padding", side_effect=lambda image, rel_box: image)
    @patch("scholarship_pipeline.ocr.pytesseract.image_to_string", return_value="ok")
    def test_extract_fields_skips_invalid_regions_without_crashing(self, mock_ocr, _mock_crop):
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("scholarship_pipeline.ocr.FIELDS", {"fallback": (0.1, 0.1, 0.1, 0.1)}), patch(
            "scholarship_pipeline.ocr.FIELDS_BY_PAGE",
            {
                2: {
                    "valid_field": (0.2, 0.2, 0.1, 0.1),
                    "invalid_field": (...),
                }
            },
        ):
            data = extract_fields_regions(image, page_number=2)

        self.assertEqual(data["valid_field"], "ok")
        self.assertEqual(data["invalid_field"], "")
        self.assertEqual(mock_ocr.call_count, 1)


if __name__ == "__main__":
    unittest.main()
