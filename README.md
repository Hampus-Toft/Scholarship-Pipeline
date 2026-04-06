# Scholarship-Pipeline
A Python OCR project to increase productivity in the Gästrike Hälsinge Nation scholarship

## Test Harness

The project now includes a local-only test harness that uses CSV output for regression checks.

Run the tests with:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py'
```

## Test Inputs

Test data lives under [test_inputs](test_inputs) and is organized by applicant bundle.

Current bundles:

- [test_inputs/applicant_bundle_5_page](test_inputs/applicant_bundle_5_page)
- [test_inputs/applicant_bundle_2_page](test_inputs/applicant_bundle_2_page)

Bundle data is split into:

- Application folders for the scholarship-related form types
- Shared attachments that may be reused across multiple applications in the same bundle
- Optional attachments that are best-effort only

The bundle index is stored in [test_inputs/bundles.csv](test_inputs/bundles.csv), and each bundle has a manifest CSV describing the expected document groups and reuse rules.

## JPEG Pair Benchmark (2-page samples)

For quick benchmarking with two separate JPEG files per sample (page 1 + page 2):

1. Put images in [test_inputs/applicant_bundle_2_page/jpeg_samples](test_inputs/applicant_bundle_2_page/jpeg_samples).
2. Register each pair in [test_inputs/applicant_bundle_2_page/jpeg_pairs.csv](test_inputs/applicant_bundle_2_page/jpeg_pairs.csv).
3. Optionally set `expected_answers_relpath` per sample if you want field-level accuracy scoring.
4. Run:

```bash
uv run python tests/run_jpeg_pair_benchmark.py
```

By default, JPEG runners disable perspective correction (`SP_DISABLE_WARP=1`) to avoid accidental zoom-in on already scan-like A4 images.
If you want to force perspective correction during JPEG runs, set:

```bash
SP_JPEG_PAIR_USE_WARP=1 uv run python tests/run_jpeg_pair_benchmark.py
```

Results are written to [test_outputs/jpeg_pair_benchmark_results.csv](test_outputs/jpeg_pair_benchmark_results.csv).

For side-by-side comparisons, set a tag so each run writes a separate file:

```bash
SP_BENCHMARK_TAG=warp_on uv run python tests/run_jpeg_pair_benchmark.py
SP_DISABLE_WARP=1 SP_BENCHMARK_TAG=warp_off uv run python tests/run_jpeg_pair_benchmark.py
```

If you want field-by-field expected vs actual differences (instead of only summary metrics), run:

```bash
uv run python tests/run_jpeg_pair_diff_report.py
```

This writes:

- [test_outputs/jpeg_pair_diff_report.csv](test_outputs/jpeg_pair_diff_report.csv): one row per compared field with `match`, `mismatch`, or `missing_field`
- [test_outputs/jpeg_pair_parsed_rows.csv](test_outputs/jpeg_pair_parsed_rows.csv): parsed merged output rows per sample
