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


def run_sample(bundle_root, sample):
    page_1 = bundle_root / sample["page_1_relpath"]
    page_2 = bundle_root / sample["page_2_relpath"]

    if not page_1.exists() or not page_2.exists():
        return None, [
            {
                "sample_id": sample["sample_id"],
                "field": "<input>",
                "status": "missing_input",
                "expected": "",
                "actual": f"Missing page file(s): {page_1} / {page_2}",
            }
        ]

    page_records = []

    extracted_1 = process_document(str(page_1), page_number=1)
    page_records.append(finalize_record(extracted_1, source_file=page_1.name, source_page=1))

    extracted_2 = process_document(str(page_2), page_number=2)
    page_records.append(finalize_record(extracted_2, source_file=page_2.name, source_page=2))

    merged = merge_page_records(page_records)

    expected_relpath = sample.get("expected_answers_relpath", "")
    if not expected_relpath:
        return merged, [
            {
                "sample_id": sample["sample_id"],
                "field": "<expected>",
                "status": "missing_expected",
                "expected": "",
                "actual": "No expected_answers_relpath set in jpeg_pairs.csv",
            }
        ]

    expected_path = bundle_root / expected_relpath
    if not expected_path.exists():
        return merged, [
            {
                "sample_id": sample["sample_id"],
                "field": "<expected>",
                "status": "missing_expected",
                "expected": "",
                "actual": f"Expected file not found: {expected_path}",
            }
        ]

    expected = load_expected(expected_path)

    rows = []
    for field in sorted(expected.keys()):
        expected_value = normalize(expected.get(field, ""))

        if field not in merged:
            rows.append(
                {
                    "sample_id": sample["sample_id"],
                    "field": field,
                    "status": "missing_field",
                    "expected": expected_value,
                    "actual": "",
                }
            )
            continue

        actual_value = normalize(merged.get(field, ""))
        status = "match" if actual_value == expected_value else "mismatch"
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "field": field,
                "status": status,
                "expected": expected_value,
                "actual": actual_value,
            }
        )

    return merged, rows


def print_summary(sample_id, diff_rows):
    matches = sum(1 for row in diff_rows if row["status"] == "match")
    mismatches = sum(1 for row in diff_rows if row["status"] == "mismatch")
    missing = sum(1 for row in diff_rows if row["status"] == "missing_field")
    issues = [row for row in diff_rows if row["status"] in {"mismatch", "missing_field", "missing_input", "missing_expected"}]

    print(f"\n=== {sample_id} ===")
    print(f"match={matches} mismatch={mismatches} missing={missing}")

    if not issues:
        print("All expected fields matched.")
        return

    print("Differences:")
    for row in issues:
        print(f"- {row['field']}: expected='{row['expected']}' actual='{row['actual']}' status={row['status']}")


def main():
    if os.getenv("SP_JPEG_PAIR_USE_WARP", "0") != "1" and "SP_DISABLE_WARP" not in os.environ:
        os.environ["SP_DISABLE_WARP"] = "1"
        print("[INFO] JPEG pair diff default: SP_DISABLE_WARP=1")

    bundle_root = REPO_ROOT / "test_inputs" / "applicant_bundle_2_page"
    pairs_csv = bundle_root / "jpeg_pairs.csv"

    if not pairs_csv.exists():
        raise FileNotFoundError(f"Missing pairs config: {pairs_csv}")

    configure_binaries()
    pairs = load_pairs(pairs_csv)

    if not pairs:
        raise ValueError("No valid sample pairs found in jpeg_pairs.csv")

    diff_rows = []
    parsed_rows = []

    for sample in pairs:
        merged, rows = run_sample(bundle_root, sample)
        diff_rows.extend(rows)

        if merged is not None:
            parsed_rows.append({"sample_id": sample["sample_id"], **merged})

        print_summary(sample["sample_id"], rows)

    output_dir = REPO_ROOT / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    diff_csv = output_dir / "jpeg_pair_diff_report.csv"
    with diff_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "field", "status", "expected", "actual"])
        writer.writeheader()
        writer.writerows(diff_rows)

    parsed_csv = output_dir / "jpeg_pair_parsed_rows.csv"
    if parsed_rows:
        headers = sorted({key for row in parsed_rows for key in row.keys()})
        with parsed_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(parsed_rows)

    print(f"\nSaved diff report to {diff_csv}")
    print(f"Saved parsed rows to {parsed_csv}")


if __name__ == "__main__":
    main()
