import cv2
import numpy as np
import pytesseract
import pandas as pd
import os
import re
from pdf2image import convert_from_path

# ---------------------------
# CONFIG
# ---------------------------

# MODE = "full_text"
MODE = "regions"

TARGET_SIZE = (2480, 3508)  # A4 at ~200 DPI (adjust if needed)

# If needed (Mac path)
pytesseract.pytesseract.tesseract_cmd = "/opt/local/bin/tesseract"

FIELDS = {
    "name": (0.15441, 0.29852, 0.34033, 0.0171),

    "personal_number_1": (0.2113, 0.3210, 0.0738, 0.0125),
    "personal_number_2": (0.2903, 0.3210, 0.0476, 0.0128),

    "birth_place": (0.1198, 0.3526, 0.7137, 0.0151),
    "is_citizen": (0.2649, 0.3777, 0.0335, 0.0105),
    "is_not_citizen": (0.3286, 0.3749, 0.0472, 0.0162),

    "period_is_ht": (0.1395, 0.3960, 0.0266, 0.0134),
    "period_is_vt": (0.1710, 0.3945, 0.0258, 0.0143),
    "period_year": (0.1996, 0.3945, 0.0246, 0.0140),

    "scholarships": (0.1157, 0.4085, 0.7331, 0.0687),

    "highschool": (0.3460, 0.4749, 0.1984, 0.0154),
    "hs_day": (0.5649, 0.4763, 0.0194, 0.0137),
    "hs_month": (0.5867, 0.4766, 0.0198, 0.0140),
    "hs_year": (0.6202, 0.4752, 0.0387, 0.0157),

    "hs_alternatives": (0.4601, 0.5202, 0.1976, 0.0188),
    "hsa_day": (0.7319, 0.5259, 0.0210, 0.0111),
    "hsa_month": (0.7552, 0.5228, 0.0190, 0.0168),
    "hsa_year": (0.7778, 0.5228, 0.0484, 0.0171),

    "uu_joined_ht": (0.3641, 0.5553, 0.0250, 0.0174),
    "uu_joined_vt": (0.3984, 0.5596, 0.0230, 0.0111),
    "uu_joined_year": (0.4246, 0.5550, 0.1294, 0.0123),

    "gh_joined_ht": (0.4000, 0.5767, 0.0238, 0.0134),
    "gh_joined_vt": (0.4331, 0.5773, 0.0214, 0.0108),
    "gh_joined_year": (0.4560, 0.5730, 0.0984, 0.0123),

    "nation_membership_1": (0.5778, 0.5924, 0.1492, 0.0140),
    "nation_membership_2": (0.1234, 0.6058, 0.6335, 0.0468),

    "other_periods_1": (0.4270, 0.6474, 0.3286, 0.0154),
    "other_periods_2": (0.1222, 0.6613, 0.6375, 0.0214),

    "break_periods_1": (0.2883, 0.6807, 0.4613, 0.0134),
    "break_periods_2": (0.1246, 0.6990, 0.6258, 0.0148),

    "credits_total": (0.2516, 0.7443, 0.1161, 0.0148),
    "credits_high": (0.1875, 0.7645, 0.1185, 0.0174),
    "credits_capped": (0.1790, 0.7816, 0.1242, 0.0154),
    "credits_high_level": (0.2597, 0.8007, 0.1141, 0.0188),

    "external_credits_total": (0.2508, 0.8421, 0.1206, 0.0097),
    "external_credits_high": (0.1851, 0.8552, 0.1198, 0.0145),
    "external_credits_capped": (0.1835, 0.8751, 0.1190, 0.0194),
    "external_credits_high_level": (0.2589, 0.8920, 0.1109, 0.0151),
}

PADDING = 0.00

# ---------------------------
# PREPROCESSING
# ---------------------------
def normalize_image(image):
    return cv2.resize(image, TARGET_SIZE)

def find_document_contour(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

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

    (tl, tr, br, bl) = rect

    width = TARGET_SIZE[0]
    height = TARGET_SIZE[1]

    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (width, height))

    return warped

def preprocess_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    original = image.copy()

    # Try to detect document contour
    contour = find_document_contour(image)

    if contour is not None:
        try:
            warped = warp_perspective(image, contour)

            # sanity check: avoid blank result
            if warped.mean() > 240:  # too white → bad warp
                print("[WARNING] Warp too bright, skipping")
                image = original
            else:
                image = warped
                print("[INFO] Perspective correction applied")

        except Exception as e:
            print(f"[WARNING] Warp failed: {e}")
            image = original
    else:
        print("[INFO] No contour found, skipping warp")

    # Resize AFTER warp decision
    image = cv2.resize(image, TARGET_SIZE)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    cv2.imwrite("debug_processed_thresh.jpg", thresh)
    cv2.imwrite("debug_processed_gray.jpg", gray)

    return gray


def pdf_to_images(pdf_path):
    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path="/opt/local/bin"  # 👈 IMPORTANT FIX
    )

    image_paths = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_base_name = re.sub(r"[^A-Za-z0-9_-]", "_", base_name)

    for i, img in enumerate(images):
        temp_path = f"temp_{safe_base_name}_page_{i}.jpg"
        img.save(temp_path, "JPEG")
        image_paths.append(temp_path)

    return image_paths

# ---------------------------
# CROP RELATIVE
# ---------------------------
def crop_with_padding(image, rel_box):
    h, w = image.shape[:2]

    x = int((rel_box[0] - PADDING) * w)
    y = int((rel_box[1] - PADDING) * h)
    ww = int((rel_box[2] + 2 * PADDING) * w)
    hh = int((rel_box[3] + 2 * PADDING) * h)

    # Clamp values
    x = max(0, x)
    y = max(0, y)

    return image[y:y+hh, x:x+ww]


# ---------------------------
# OCR FUNCTION
# ---------------------------
def ocr_full_page(image):
    config = "--oem 3 --psm 6 -l swe"
    text = pytesseract.image_to_string(image, config=config)
    return text

def parse_full_text(text):
    data = {}

    # Clean text
    text = text.replace("\n", " ").replace("  ", " ")

    # Define patterns based on known labels in your form
    patterns = {
        "name": r"Namn[: ]+([A-Za-zÅÄÖåäö\s\-]+)",
        "email": r"E-?post[: ]+([\w\.-]+@[\w\.-]+)",
        "phone": r"Telefon[: ]+([\d\s\-]+)",
        "personal_number": r"Personnummer[: ]+([\d\-]+)",
        "address": r"Adress[: ]+([A-Za-z0-9ÅÄÖåäö\s\-,]+)",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        data[field] = match.group(1).strip() if match else ""

    return data

# ---------------------------
# FIELD EXTRACTION
# ---------------------------
def extract_fields_regions(image):
    data = {}

    for field, rel_box in FIELDS.items():
        cropped = crop_with_padding(image, rel_box)

        config = "--oem 3 --psm 6 -l swe"
        text = pytesseract.image_to_string(cropped, config=config)

        data[field] = text.strip()

    return data

# ---------------------------
# Output stripping
# ---------------------------

def clean_number(text):
    """Keep only digits"""
    return re.sub(r"[^0-9]", "", text)


def clean_date_part(text):
    """Extract 1–2 digit numbers (day/month)"""
    match = re.search(r"\d{1,2}", text)
    return match.group(0) if match else ""


def clean_year(text):
    """Extract 4-digit year"""
    match = re.search(r"\d{4}", text)
    return match.group(0) if match else ""


def clean_personal_number(text):
    """Swedish personal number (YYYYMMDD-XXXX or similar)"""
    digits = re.sub(r"[^0-9]", "", text)

    if len(digits) >= 8:
        return digits[:8]  # you can extend to 12 if needed
    return digits


def clean_checkbox(text):
    """Normalize checkbox OCR"""
    text = text.lower()
    if "ja" in text:
        return "Ja"
    if "nej" in text:
        return "Nej"
    return ""



def clean_data(data):
    return {
        **data,
        "personal_number_1": clean_number(data.get("personal_number_1", "")),
        "personal_number_2": clean_number(data.get("personal_number_2", "")),

        "hs_day": clean_date_part(data.get("hs_day", "")),
        "hs_month": clean_date_part(data.get("hs_month", "")),
        "hs_year": clean_year(data.get("hs_year", "")),

        "hsa_day": clean_date_part(data.get("hsa_day", "")),
        "hsa_month": clean_date_part(data.get("hsa_month", "")),
        "hsa_year": clean_year(data.get("hsa_year", "")),

        "is_citizen": clean_checkbox(data.get("is_citizen", "")),
        "is_not_citizen": clean_checkbox(data.get("is_not_citizen", "")),

        "credits_total": clean_number(data.get("credits_total", "")),
        "credits_high": clean_number(data.get("credits_high", "")),
        "credits_capped": clean_number(data.get("credits_capped", "")),
        "credits_high_level": clean_number(data.get("credits_high_level", "")),

        "external_credits_total": clean_number(data.get("external_credits_total", "")),
        "external_credits_high": clean_number(data.get("external_credits_high", "")),
        "external_credits_capped": clean_number(data.get("external_credits_capped", "")),
        "external_credits_high_level": clean_number(data.get("external_credits_high_level", "")),
    }

def merge_split_fields(data):
    merged = {}
    used_keys = set()

    for key in data:
        if key.endswith("_1"):
            base = key[:-2]
            part1 = data.get(f"{base}_1", "")
            part2 = data.get(f"{base}_2", "")

            merged_value = f"{part1} {part2}".strip()

            merged[base] = merged_value
            used_keys.add(f"{base}_1")
            used_keys.add(f"{base}_2")

        elif key.endswith("_2"):
            continue

        else:
            if key not in used_keys:
                merged[key] = data[key]

    return merged

# ---------------------------
# PROCESS DOCUMENT
# ---------------------------
def process_document(image_path):
    processed = preprocess_image(image_path)

    if MODE == "full_text":
        full_text = ocr_full_page(processed)
        data = parse_full_text(full_text)

    elif MODE == "regions":
        data = extract_fields_regions(processed)

    else:
        raise ValueError("Invalid MODE")

    return data


# ---------------------------
# SAVE TO EXCEL
# ---------------------------

def save_to_excel(data_list, output_file="output.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(output_file, index=False)
    print(f"[INFO] Saved to {output_file}")

# --------------------------
# Post processing
# --------------------------
def score_field(value, field_name):
    if not value or len(value.strip()) == 0:
        return 0.0

    score = 1.0

    # Penalize weird characters
    if re.search(r"[^\w\s\-\@\.\,]", value):
        score -= 0.2

    # Penalize too many random letters in numeric fields
    if "number" in field_name or "year" in field_name or "day" in field_name:
        if re.search(r"[A-Za-z]", value):
            score -= 0.4

    # Penalize short values
    if len(value.strip()) < 3:
        score -= 0.3

    # Penalize obvious OCR noise
    if "..." in value or "aaa" in value.lower():
        score -= 0.3

    return max(score, 0.0)

def score_data(data):
    scores = {}
    total_score = 0

    for key, value in data.items():
        field_score = score_field(value, key)
        scores[key] = field_score
        total_score += field_score

    avg_score = total_score / len(data) if data else 0

    return scores, avg_score

def needs_review(data, scores, threshold=0.6):
    flagged = []

    for key, value in data.items():
        if not value or scores[key] < threshold:
            flagged.append(key)

    return flagged


def finalize_record(data, source_file, source_page=None):
    cleaned = clean_data(data)
    merged = merge_split_fields(cleaned)
    scores, avg_score = score_data(merged)
    flags = needs_review(merged, scores)

    merged["confidence_avg"] = round(avg_score, 2)
    merged["needs_review"] = len(flags) > 0
    merged["flagged_fields"] = ", ".join(flags)
    merged["source_file"] = source_file

    if source_page is not None:
        merged["source_page"] = source_page

    return merged

# ---------------------------
# MAIN
# ---------------------------

if __name__ == "__main__":
    input_folder = "input_images"
    results = []

    for file in sorted(os.listdir(input_folder)):
        path = os.path.join(input_folder, file)

        print(f"[INFO] Processing {file}")

        if file.lower().endswith(".pdf"):
            image_paths = pdf_to_images(path)

            for page_number, img_path in enumerate(image_paths, start=1):
                try:
                    data = process_document(img_path)
                    finalized = finalize_record(data, source_file=file, source_page=page_number)
                    results.append(finalized)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            data = process_document(path)
            finalized = finalize_record(data, source_file=file)
            results.append(finalized)

    save_to_excel(results)
    print(results)