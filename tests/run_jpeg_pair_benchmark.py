import csv
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scholarship_pipeline.config import configure_binaries
from scholarship_pipeline.pipeline import process_document
from scholarship_pipeline.postprocess import finalize_record, merge_page_records


def load_pairs(csv_path):
    pairs = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sample_id = (row.get("sample_id") or "").strip()
            page_1 = (row.get("page_1_relpath") or "").strip()
            page_2 = (row.get("page_2_relpath") or "").strip()
            expected = (row.get("expected_answers_relpath") or "").strip()

            if not sample_id or not page_1 or not page_2:
                continue

            pairs.append(
                {
                    "sample_id": sample_id,
                    "page_1_relpath": page_1,
                    "page_2_relpath": page_2,
                    "expected_answers_relpath": expected,
                }
            )

    return pairs


def load_expected(expected_path):
    expected = {}

    with expected_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, skipinitialspace=True)
        _ = next(reader, None)

        for row in reader:
            if not row:
                continue

            field = row[0].strip() if len(row) > 0 else ""
            value = row[1].strip() if len(row) > 1 else ""

            if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                value = value[1:-1]

            if field and value:
                expected[field] = value

    return expected


def normalize(value):
    if value is None:
        return ""

    text = str(value).strip()

    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1].strip()

    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def compare_record(merged, expected):
    missing = 0
    mismatches = 0
    matched = 0

    for field, expected_value in expected.items():
        if field not in merged:
            missing += 1
            continue

        actual = normalize(merged.get(field))
        if actual == normalize(expected_value):
            matched += 1
        else:
            mismatches += 1

    total = len(expected)
    compared = matched + mismatches
    score = round((matched / total) * 100, 2) if total else 0.0

    return {
        "expected_fields": total,
        "matched_fields": matched,
        "mismatched_fields": mismatches,
        "missing_fields": missing,
        "match_score_pct": score,
        "compared_fields": compared,
    }


def run_sample(bundle_root, sample):
    page_1 = bundle_root / sample["page_1_relpath"]
    page_2 = bundle_root / sample["page_2_relpath"]

    if not page_1.exists() or not page_2.exists():
        return {
            "sample_id": sample["sample_id"],
            "status": "missing_input",
            "message": f"Missing page file(s): {page_1} / {page_2}",
        }

    page_records = []

    extracted_1 = process_document(str(page_1), page_number=1)
    page_records.append(finalize_record(extracted_1, source_file=page_1.name, source_page=1))

    extracted_2 = process_document(str(page_2), page_number=2)
    page_records.append(finalize_record(extracted_2, source_file=page_2.name, source_page=2))

    merged = merge_page_records(page_records)
    result = {
        "sample_id": sample["sample_id"],
        "status": "ok",
        "page_count": merged.get("page_count", ""),
        "confidence_avg": merged.get("confidence_avg", ""),
        "needs_review": merged.get("needs_review", ""),
        "flagged_fields": merged.get("flagged_fields", ""),
    }

    expected_relpath = sample.get("expected_answers_relpath", "")
    if expected_relpath:
        expected_path = bundle_root / expected_relpath
        if expected_path.exists():
            expected = load_expected(expected_path)
            metrics = compare_record(merged, expected)
            result.update(metrics)
        else:
            result["status"] = "missing_expected"
            result["message"] = f"Expected file not found: {expected_path}"

    return result


def main():
    if os.getenv("SP_JPEG_PAIR_USE_WARP", "0") != "1" and "SP_DISABLE_WARP" not in os.environ:
        os.environ["SP_DISABLE_WARP"] = "1"
        print("[INFO] JPEG pair benchmark default: SP_DISABLE_WARP=1")

    repo_root = REPO_ROOT
    bundle_root = repo_root / "test_inputs" / "applicant_bundle_2_page"
    pairs_csv = bundle_root / "jpeg_pairs.csv"

    if not pairs_csv.exists():
        raise FileNotFoundError(f"Missing pairs config: {pairs_csv}")

    configure_binaries()
    pairs = load_pairs(pairs_csv)

    if not pairs:
        raise ValueError("No valid sample pairs found in jpeg_pairs.csv")

    results = [run_sample(bundle_root, sample) for sample in pairs]

    output_dir = repo_root / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    tag = os.getenv("SP_BENCHMARK_TAG", "").strip()
    filename = "jpeg_pair_benchmark_results.csv"
    if tag:
        filename = f"jpeg_pair_benchmark_results_{tag}.csv"

    output_csv = output_dir / filename

    headers = sorted({key for row in results for key in row.keys()})

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved benchmark results to {output_csv}")
    for row in results:
        print(row)


if __name__ == "__main__":
    main()
