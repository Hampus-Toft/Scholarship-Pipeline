import re


def clean_number(text):
    return re.sub(r"[^0-9]", "", text)


def clean_date_part(text):
    match = re.search(r"\d{1,2}", text)
    return match.group(0) if match else ""


def clean_year(text):
    match = re.search(r"\d{4}", text)
    return match.group(0) if match else ""


def clean_checkbox(text):
    normalized = text.lower()
    if "ja" in normalized:
        return "Ja"
    if "nej" in normalized:
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
            merged[base] = f"{part1} {part2}".strip()
            used_keys.add(f"{base}_1")
            used_keys.add(f"{base}_2")
        elif key.endswith("_2"):
            continue
        elif key not in used_keys:
            merged[key] = data[key]

    return merged


def score_field(value, field_name):
    if not value or len(value.strip()) == 0:
        return 0.0

    score = 1.0

    if re.search(r"[^\w\s\-\@\.\,]", value):
        score -= 0.2

    if "number" in field_name or "year" in field_name or "day" in field_name:
        if re.search(r"[A-Za-z]", value):
            score -= 0.4

    if len(value.strip()) < 3:
        score -= 0.3

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
