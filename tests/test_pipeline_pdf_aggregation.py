import unittest
from unittest.mock import patch

from scholarship_pipeline.pipeline import run_pipeline


class PipelinePdfAggregationTests(unittest.TestCase):
    @patch("scholarship_pipeline.pipeline.save_output")
    @patch("scholarship_pipeline.pipeline.finalize_record")
    @patch("scholarship_pipeline.pipeline.process_document")
    @patch("scholarship_pipeline.pipeline.pdf_to_images")
    @patch("scholarship_pipeline.pipeline.configure_binaries")
    @patch("scholarship_pipeline.pipeline.os.remove")
    @patch("scholarship_pipeline.pipeline.os.path.exists", return_value=True)
    @patch("scholarship_pipeline.pipeline.os.listdir", return_value=["applicant.pdf"])
    def test_pdf_is_exported_as_single_merged_row(
        self,
        _mock_listdir,
        _mock_exists,
        _mock_remove,
        _mock_configure,
        mock_pdf_to_images,
        mock_process_document,
        mock_finalize_record,
        mock_save_output,
    ):
        mock_pdf_to_images.return_value = ["temp_page_1.jpg", "temp_page_2.jpg"]
        mock_process_document.side_effect = [
            {"name": "Alice", "period_year": "2025"},
            {"bank": "SEB", "period_year": "2026"},
        ]
        mock_finalize_record.side_effect = [
            {
                "source_file": "applicant.pdf",
                "source_page": 1,
                "confidence_avg": 0.8,
                "needs_review": False,
                "flagged_fields": "",
                "name": "Alice",
                "period_year": "2025",
            },
            {
                "source_file": "applicant.pdf",
                "source_page": 2,
                "confidence_avg": 0.6,
                "needs_review": True,
                "flagged_fields": "bank",
                "bank": "SEB",
                "period_year": "2026",
            },
        ]

        results = run_pipeline(input_folder="input_images", output_file="output.csv")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_file"], "applicant.pdf")
        self.assertEqual(results[0]["source_pages"], "1,2")
        self.assertEqual(results[0]["page_count"], 2)
        self.assertEqual(results[0]["name"], "Alice")
        self.assertEqual(results[0]["bank"], "SEB")
        self.assertEqual(results[0]["period_year"], "2025")
        self.assertEqual(results[0]["page_2_period_year"], "2026")

        mock_save_output.assert_called_once()


if __name__ == "__main__":
    unittest.main()
