from scholarship_pipeline.postprocess import finalize_record, merge_page_records


def test_finalize_record_marks_low_quality_fields_for_review():
    data = {
        "name": "Alice Example",
        "personal_number_1": "1234",
        "credits_total": "12a",
    }

    record = finalize_record(data, source_file="sample.pdf", source_page=3)

    assert record["source_file"] == "sample.pdf"
    assert record["source_page"] == 3
    assert record["needs_review"] is True
    assert "credits_total" in record["flagged_fields"]
    assert record["confidence_avg"] <= 1.0


def test_finalize_record_keeps_clean_values():
    data = {
        "name": "Alice Example",
        "personal_number_1": "123 45",
        "personal_number_2": "6789",
        "is_citizen": "Ja",
    }

    record = finalize_record(data, source_file="sample.pdf")

    assert record["personal_number_1"] == "12345"
    assert record["is_citizen"] == "Ja"
    assert record["needs_review"] is False


def test_merge_page_records_combines_pdf_pages_into_single_row():
    page_1 = {
        "source_file": "sample.pdf",
        "source_page": 1,
        "confidence_avg": 0.8,
        "needs_review": False,
        "flagged_fields": "",
        "name": "Alice Example",
        "period_year": "2025",
    }
    page_2 = {
        "source_file": "sample.pdf",
        "source_page": 2,
        "confidence_avg": 0.6,
        "needs_review": True,
        "flagged_fields": "bank",
        "bank": "SEB",
        "period_year": "2026",
    }

    merged = merge_page_records([page_1, page_2])

    assert merged["source_file"] == "sample.pdf"
    assert merged["source_pages"] == "1,2"
    assert merged["page_count"] == 2
    assert merged["name"] == "Alice Example"
    assert merged["bank"] == "SEB"
    assert merged["period_year"] == "2025"
    assert merged["page_2_period_year"] == "2026"
    assert merged["needs_review"] is True
    assert merged["flagged_fields"] == "bank"
    assert merged["confidence_avg"] == 0.7
