# Expected Answers

Fill [expected_answers.csv](expected_answers.csv) with the correct values from the 2-page scholarship sample.

For JPEG pair benchmarking, fill these separately:

- [expected_answers_sample_1.csv](expected_answers_sample_1.csv)
- [expected_answers_sample_2.csv](expected_answers_sample_2.csv)

How this is used:
- `field`: output key from the merged pipeline row
- `expected_value`: the known-correct value
- `notes`: optional context

The pipeline currently outputs one merged row per PDF with metadata fields like `source_file`, `source_pages`, and `page_count`.
