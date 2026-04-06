import cv2
import numpy as np

from .config import TARGET_SIZE


def normalize_image(image):
    return cv2.resize(image, TARGET_SIZE)


def find_document_contour(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            return approx

    return None


def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def warp_perspective(image, contour):
    rect = order_points(contour)
    width = TARGET_SIZE[0]
    height = TARGET_SIZE[1]

    dst = np.array(
        [
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1],
        ],
        dtype="float32",
    )

    transform = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, transform, (width, height))

    return warped


def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    original = image.copy()
    contour = find_document_contour(image)

    if contour is not None:
        try:
            warped = warp_perspective(image, contour)
            if warped.mean() > 240:
                print("[WARNING] Warp too bright, skipping")
                image = original
            else:
                image = warped
                print("[INFO] Perspective correction applied")
        except Exception as exc:
            print(f"[WARNING] Warp failed: {exc}")
            image = original
    else:
        print("[INFO] No contour found, skipping warp")

    image = cv2.resize(image, TARGET_SIZE)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )

    cv2.imwrite("debug_processed_thresh.jpg", thresh)
    cv2.imwrite("debug_processed_gray.jpg", gray)

    return gray
