import os

import cv2
import numpy as np

from .config import TARGET_SIZE


def is_a4_like_scan(image):
    h, w = image.shape[:2]
    if h == 0 or w == 0:
        return False

    target_w, target_h = TARGET_SIZE

    input_ratio = w / h
    target_ratio = target_w / target_h

    # Accept modest size variance but require near-A4 aspect ratio.
    ratio_delta = abs(input_ratio - target_ratio)
    width_scale = w / target_w
    height_scale = h / target_h

    size_is_reasonable = 0.8 <= width_scale <= 1.25 and 0.8 <= height_scale <= 1.25
    return ratio_delta <= 0.03 and size_is_reasonable


def normalize_image(image):
    return cv2.resize(image, TARGET_SIZE)


def contour_to_quad(contour):
    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

    if len(approx) == 4:
        return approx

    # Fallback: use minimum-area rectangle so non-perfect page edges can still be warped.
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    return box.reshape(-1, 1, 2).astype(np.float32)


def contour_score(contour, image_shape):
    h, w = image_shape[:2]
    image_area = float(h * w)
    if image_area <= 0:
        return -1.0

    contour_area = cv2.contourArea(contour)
    area_ratio = contour_area / image_area
    if area_ratio < 0.25:
        return -1.0

    x, y, cw, ch = cv2.boundingRect(contour)
    if cw == 0 or ch == 0:
        return -1.0

    target_w, target_h = TARGET_SIZE
    target_aspect = min(target_w, target_h) / max(target_w, target_h)
    contour_aspect = min(cw, ch) / max(cw, ch)
    aspect_penalty = abs(contour_aspect - target_aspect)

    edge_margin = max(8, int(min(h, w) * 0.01))
    touches_edges = 0
    if x <= edge_margin:
        touches_edges += 1
    if y <= edge_margin:
        touches_edges += 1
    if x + cw >= w - edge_margin:
        touches_edges += 1
    if y + ch >= h - edge_margin:
        touches_edges += 1

    # Favor large contours that look A4-like and touch image boundaries.
    # Area has the highest weight to avoid selecting inner form boxes.
    score = (area_ratio * 8.0) + (touches_edges * 0.35) - (aspect_penalty * 2.5)
    return score


def find_document_contour(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    kernel = np.ones((5, 5), np.uint8)
    edged = cv2.dilate(edged, kernel, iterations=1)
    edged = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best_contour = None
    best_score = -1.0

    # Limit to the largest contours for speed/stability on noisy scans.
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:25]:
        score = contour_score(contour, image.shape)
        if score > best_score:
            best_score = score
            best_contour = contour

    if best_contour is None:
        return None

    return contour_to_quad(best_contour)


def contour_area_ratio(contour, image_shape):
    h, w = image_shape[:2]
    image_area = float(h * w)
    if image_area <= 0:
        return 0.0

    return cv2.contourArea(contour) / image_area


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
    disable_warp = os.getenv("SP_DISABLE_WARP", "0") == "1"
    force_warp = os.getenv("SP_FORCE_WARP", "0") == "1"
    min_warp_area_ratio = float(os.getenv("SP_WARP_MIN_AREA_RATIO", "0.35"))

    if disable_warp:
        print("[INFO] Perspective correction disabled by SP_DISABLE_WARP=1")
        image = original
    elif is_a4_like_scan(image) and not force_warp:
        print("[INFO] Input already A4-like; skipping perspective correction")
        image = original
    else:
        contour = find_document_contour(image)

        if contour is not None:
            try:
                area_ratio = contour_area_ratio(contour, image.shape)

                if area_ratio < min_warp_area_ratio and not force_warp:
                    print(
                        f"[WARNING] Contour too small for page warp (area_ratio={area_ratio:.2f} < {min_warp_area_ratio:.2f}), skipping"
                    )
                    image = original
                else:
                    print(f"[INFO] Selected contour area ratio: {area_ratio:.2f}")
                    warped = warp_perspective(image, contour)

                if image is original:
                    pass
                elif warped.mean() > 240:
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
