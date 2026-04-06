import re

import pytesseract

from .config import FIELDS, FIELDS_BY_PAGE, MODE, PADDING


def is_valid_rel_box(rel_box):
    if not isinstance(rel_box, (tuple, list)):
        return False

    if len(rel_box) != 4:
        return False

    return all(isinstance(value, (int, float)) for value in rel_box)


def crop_with_padding(image, rel_box):
    h, w = image.shape[:2]

    x = int((rel_box[0] - PADDING) * w)
    y = int((rel_box[1] - PADDING) * h)
    ww = int((rel_box[2] + 2 * PADDING) * w)
    hh = int((rel_box[3] + 2 * PADDING) * h)

    x = max(0, x)
    y = max(0, y)

    return image[y : y + hh, x : x + ww]


def ocr_full_page(image):
    config = "--oem 3 --psm 6 -l swe"
    return pytesseract.image_to_string(image, config=config)


def parse_full_text(text):
    data = {}
    text = text.replace("\n", " ").replace("  ", " ")

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


def extract_fields_regions(image, page_number=None):
    data = {}
    fields = FIELDS_BY_PAGE.get(page_number, FIELDS)

    for field, rel_box in fields.items():
        if not is_valid_rel_box(rel_box):
            print(
                f"[WARNING] Invalid region for field '{field}' on page {page_number}: {rel_box}. Skipping field."
            )
            data[field] = ""
            continue

        cropped = crop_with_padding(image, rel_box)
        config = "--oem 3 --psm 6 -l swe"
        text = pytesseract.image_to_string(cropped, config=config)
        data[field] = text.strip()

    return data


def extract_data(processed_image, page_number=None):
    if MODE == "full_text":
        full_text = ocr_full_page(processed_image)
        return parse_full_text(full_text)

    if MODE == "regions":
        return extract_fields_regions(processed_image, page_number=page_number)

    raise ValueError("Invalid MODE")
