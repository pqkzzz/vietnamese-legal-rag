"""Unit tests for legal document normalization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.legal_parser.normalizer import normalize_document


def make_raw_document() -> dict:
    return {
        "law_info": {
            "law_id": "LTEST_2024",
            "law_name": "Luật Thử nghiệm 2024 (Văn bản hợp nhất 01/VBHN-VPQH 2025)",
            "publisher": "Văn phòng Quốc hội",
            "document_number": "01/VBHN-VPQH",
            "issue_date": "28/02/2025",
            "effective_date": "2024-08-01",
            "status": "Đang có hiệu lực",
            "executive_summary": "Tóm tắt tiếng Việt.",
        },
        "clauses": [],
    }


def unit(unit_id: str, article: object = 1, clause: object = 1, content: object = "1. Nội dung") -> dict:
    return {
        "id": unit_id,
        "position": {"chapter": 1, "article": article, "article_title": "Điều thử", "clause": clause},
        "content": content,
        "cross_references": [],
        "tags": [],
    }


def normalized_units(raw: dict) -> list[dict]:
    return normalize_document(raw, "test.json")["legal_units"]


def test_article_number_integer_is_converted_to_string() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D3_K1", article=3)]

    result = normalized_units(raw)[0]

    assert result["position"]["article_number"] == "3"
    assert result["article_id"] == "LTEST_2024_D3"


def test_article_number_suffix_is_preserved() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D15a_K1", article="15a")]

    assert normalized_units(raw)[0]["position"]["article_number"] == "15a"


def test_null_clause_becomes_article() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D1", clause=None, content="Nội dung điều.")]

    result = normalized_units(raw)[0]

    assert result["unit_type"] == "article"
    assert result["parent_id"] is None


def test_zero_clause_becomes_article_lead_without_clause_number() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D2_K0", clause=0, content="Trong Điều này:")]

    result = normalized_units(raw)[0]

    assert result["unit_type"] == "article_lead"
    assert result["position"]["clause_number"] is None
    assert result["is_retrievable"] is False


def test_regular_clause_becomes_clause() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D2_K2", clause=2)]

    assert normalized_units(raw)[0]["unit_type"] == "clause"


def test_footnotes_removed_only_from_clean_content() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D3_K1", content="1. Nội dung[2] và chú thích[80].")]

    result = normalized_units(raw)[0]

    assert "[2]" in result["content_raw"]
    assert "[80]" in result["content_raw"]
    assert "[2]" not in result["content_clean"]
    assert "[80]" not in result["content_clean"]


def test_repealed_content_is_not_retrievable() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D4_K1", content="1. (được bãi bỏ)")]

    result = normalized_units(raw)[0]

    assert result["provision_status"] == "repealed"
    assert result["is_retrievable"] is False


def test_tags_are_trimmed_and_deduplicated_case_insensitively() -> None:
    raw = make_raw_document()
    row = unit("LTEST_2024_D5_K1")
    row["tags"] = [" đất đai ", "Đất Đai", "", "Nhà ở"]
    raw["clauses"] = [row]

    assert normalized_units(raw)[0]["tags"] == ["đất đai", "Nhà ở"]


def test_date_ddmmyyyy_becomes_iso() -> None:
    raw = make_raw_document()

    result = normalize_document(raw, "test.json")

    assert result["law_info"]["issue_date"] == "2025-02-28"
    assert result["law_info"]["effective_from"] == "2024-08-01"


def test_invalid_date_warns_without_crashing() -> None:
    raw = make_raw_document()
    raw["law_info"]["issue_date"] = "32/13/2025"
    raw["clauses"] = [unit("LTEST_2024_D1_K1")]

    result = normalize_document(raw, "test.json")

    assert result["law_info"]["issue_date"] is None
    assert any(warning["code"] == "INVALID_DATE" for warning in result["normalization_report"]["warnings"])
    assert len(result["legal_units"]) == 1


def test_duplicate_unit_id_is_detected_and_second_unit_excluded() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D1_K1"), unit("LTEST_2024_D1_K1")]

    result = normalize_document(raw, "test.json")

    assert len(result["legal_units"]) == 1
    assert any(error["code"] == "DUPLICATE_UNIT_ID" for error in result["normalization_report"]["errors"])


def test_missing_article_number_is_excluded_and_errors() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_DX_K1", article=None)]

    result = normalize_document(raw, "test.json")

    assert result["legal_units"] == []
    assert any(error["code"] == "MISSING_ARTICLE_NUMBER" for error in result["normalization_report"]["errors"])


def test_cross_reference_raw_is_preserved() -> None:
    raw = make_raw_document()
    row = unit("LTEST_2024_D6_K1")
    raw_ref = {
        "target_id": "LTEST_2024_D3_K2",
        "anchor_text": "khoản 2 Điều 3",
        "description_summary": "Mô tả",
    }
    row["cross_references"] = [raw_ref]
    raw["clauses"] = [row]

    result = normalized_units(raw)[0]["cross_references"][0]

    assert result["reference_type"] == "internal"
    assert result["target_article_number"] == "3"
    assert result["target_clause_number"] == "2"
    assert result["raw_reference"] == raw_ref


def test_output_json_preserves_vietnamese_unicode() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D7_K1", content="1. Quyền sử dụng đất ở Việt Nam.")]

    payload = json.dumps(normalize_document(raw, "test.json"), ensure_ascii=False)

    assert "Quyền sử dụng đất ở Việt Nam" in payload


def test_legal_unit_order_is_preserved() -> None:
    raw = make_raw_document()
    raw["clauses"] = [unit("LTEST_2024_D1_K1"), unit("LTEST_2024_D1_K2"), unit("LTEST_2024_D2_K1")]

    result = normalized_units(raw)

    assert [item["unit_id"] for item in result] == ["LTEST_2024_D1_K1", "LTEST_2024_D1_K2", "LTEST_2024_D2_K1"]
