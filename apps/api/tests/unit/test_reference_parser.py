from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import LegalReferenceParser, LegalReferenceType, ProvisionLevel, ProvisionNode


def _node(content: str = "", cross_references: list[dict[str, object]] | None = None) -> ProvisionNode:
    return ProvisionNode(
        qdrant_point_id=None,
        chunk_id="LAW_D121_K1",
        source_unit_id="LAW_D121_K1",
        unit_type="clause",
        level=ProvisionLevel.CLAUSE,
        law_id="LAW",
        law_name="Luật test",
        chapter_number=None,
        chapter_title=None,
        section_number=None,
        section_title=None,
        article_number="121",
        article_title="Điều nguồn",
        clause_number="1",
        point_number=None,
        article_id="LAW_D121",
        parent_id="LAW_D121",
        child_ids=(),
        has_children=False,
        content_raw=content,
        content_clean=content,
        clause_lead_raw=None,
        clause_lead_clean=None,
        cross_references=cross_references or [],
        tags=[],
        provision_status="effective",
        is_retrievable=True,
        document_status="effective",
        order_index=0,
        previous_sibling_id=None,
        next_sibling_id=None,
        metadata={},
    )


def test_structured_metadata_article_reference() -> None:
    parser = LegalReferenceParser()
    ref = parser.parse_structured_reference(
        _node(),
        {"reference_type": "internal", "target_law_id": "LAW", "target_article_number": "34", "anchor_text": "Điều 34"},
    )
    assert ref is not None
    assert ref.target_law_id == "LAW"
    assert ref.target_article_number == "34"
    assert ref.target_clause_number is None
    assert ref.parser_source == "structured_metadata"


def test_structured_metadata_clause_reference() -> None:
    parser = LegalReferenceParser()
    ref = parser.parse_structured_reference(
        _node(),
        {"reference_type": "internal", "target_law_id": "LAW", "target_article_number": "34", "target_clause_number": "2"},
    )
    assert ref is not None
    assert ref.target_article_number == "34"
    assert ref.target_clause_number == "2"


def test_structured_metadata_point_reference() -> None:
    parser = LegalReferenceParser()
    ref = parser.parse_structured_reference(
        _node(),
        {
            "reference_type": "internal",
            "target_law_id": "LAW",
            "target_article_number": "121",
            "target_clause_number": "1",
            "target_point_number": "b",
        },
    )
    assert ref is not None
    assert ref.target_point_number == "b"


def test_internal_reference_missing_law_uses_source_law() -> None:
    parser = LegalReferenceParser()
    ref = parser.parse_structured_reference(_node(), {"reference_type": "internal", "target_article_number": "70"})
    assert ref is not None
    assert ref.target_law_id == "LAW"


def test_target_unit_id_is_preserved() -> None:
    parser = LegalReferenceParser()
    ref = parser.parse_structured_reference(_node(), {"reference_type": "internal", "target_unit_id": "LAW_D70"})
    assert ref is not None
    assert ref.target_unit_id == "LAW_D70"


def test_parse_article_reference() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Theo Điều 34 của Luật này")
    assert [(ref.target_article_number, ref.target_clause_number, ref.target_point_number) for ref in refs] == [("34", None, None)]


def test_parse_clause_article_reference() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Theo khoản 2 Điều 34")
    assert refs[0].target_article_number == "34"
    assert refs[0].target_clause_number == "2"


def test_parse_point_clause_article_reference() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Theo điểm b khoản 1 Điều 121")
    assert refs[0].target_article_number == "121"
    assert refs[0].target_clause_number == "1"
    assert refs[0].target_point_number == "b"


def test_parse_vietnamese_dd_point() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Theo điểm đ khoản 2 Điều 30")
    assert refs[0].target_point_number == "đ"


def test_parse_multiple_articles() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Theo các Điều 34, 35 và 36")
    assert [ref.target_article_number for ref in refs] == ["34", "35", "36"]


def test_parse_relative_clause_same_article() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "theo khoản 1 Điều này")
    assert refs[0].reference_type == LegalReferenceType.RELATIVE
    assert refs[0].target_law_id == "LAW"
    assert refs[0].target_article_number == "121"
    assert refs[0].target_clause_number == "1"


def test_parse_relative_article() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "quy định tại Điều này")
    assert refs[0].reference_type == LegalReferenceType.RELATIVE
    assert refs[0].target_article_number == "121"


def test_does_not_parse_dieu_kien() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Điều kiện chuyển nhượng được quy định rõ.")
    assert refs == []


def test_does_not_parse_year_or_document_number_without_marker() -> None:
    refs = LegalReferenceParser().parse_text(_node(), "Năm 2024 và số 45/VBHN-VPQH không phải viện dẫn.")
    assert refs == []


def test_structured_and_regex_duplicates_keep_structured() -> None:
    node = _node(
        "Nội dung nhắc lại Điều 34.",
        [{"reference_type": "internal", "target_law_id": "LAW", "target_article_number": "34", "anchor_text": "Điều 34"}],
    )
    refs = LegalReferenceParser().parse_node(node)
    assert len(refs) == 1
    assert refs[0].parser_source == "structured_metadata"


def test_raw_metadata_is_preserved() -> None:
    raw = {"target_id": "LAW_D70", "anchor_text": "Điều 70"}
    ref = LegalReferenceParser().parse_structured_reference(
        _node(),
        {"reference_type": "internal", "target_unit_id": "LAW_D70", "raw_reference": raw},
    )
    assert ref is not None
    assert ref.metadata["raw_reference"] == raw
