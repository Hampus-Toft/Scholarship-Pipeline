import unittest

import cv2
import numpy as np

from scholarship_pipeline.preprocessing import find_document_contour


class PreprocessingContourTests(unittest.TestCase):
    def test_find_document_contour_prefers_outer_page_over_inner_rectangle(self):
        image = np.full((1000, 700, 3), 255, dtype=np.uint8)

        # Outer page border.
        cv2.rectangle(image, (8, 8), (692, 992), (0, 0, 0), 6)

        # Inner form rectangle that should NOT be selected as document contour.
        cv2.rectangle(image, (160, 180), (540, 760), (0, 0, 0), 6)

        contour = find_document_contour(image)
        self.assertIsNotNone(contour)

        x, y, w, h = cv2.boundingRect(contour)

        # The chosen contour should be close to the image boundaries (outer page).
        self.assertLessEqual(x, 30)
        self.assertLessEqual(y, 30)
        self.assertGreaterEqual(x + w, 670)
        self.assertGreaterEqual(y + h, 970)


if __name__ == "__main__":
    unittest.main()
