"""Tests for retrieval chunk building."""

from __future__ import annotations

from copy import deepcopy
import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.ingestion.chunk_builder import build_chunks_for_document
from scripts.build_chunks import atomic_write_jsonl


def base_document() -> dict:
    return {
        "schema_version": "1.0",
        "law_info": {
            "law_id": "LTEST_2024",
            "law_name": "Luật Thử nghiệm 2024",
            "full_name": "Luật Thử nghiệm 2024",
            "document_number": "01/VBHN-VPQH",
            "document_type": "Văn bản hợp nhất",
            "document_status": "effective",
            "issue_date": "2025-02-28",
            "effective_from": "2024-08-01",
            "effective_to": None,
            "executive_summary": "Không được đưa vào embedding.",
        },
        "legal_units": [],
    }


def unit(unit_id: str, unit_type: str, article: str = "1", clause: str | None = "1", content: str = "1. Nội dung") -> dict:
    return {
        "unit_id": unit_id,
        "source_unit_id": unit_id,
        "unit_type": unit_type,
        "position": {
            "chapter_number": "1",
            "chapter_title": None,
            "section_number": None,
            "section_title": None,
            "article_number": article,
            "article_title": "Phạm vi điều chỉnh",
            "clause_number": clause,
            "point_number": None,
        },
        "article_id": f"LTEST_2024_D{article}",
        "parent_id": None if unit_type == "article" else f"LTEST_2024_D{article}",
        "content_raw": content,
        "content_clean": content,
        "cross_references": [{"target_id": "LTEST_2024_D1", "anchor_text": "Điều 1"}],
        "tags": ["đất đai"],
        "provision_status": "effective",
        "is_retrievable": unit_type != "article_lead",
        "source": {"source_file": "test.json", "source_url": None},
    }


def build_sample() -> tuple[dict, list[dict], dict]:
    doc = base_document()
    point_clause = "2. Các trường hợp sau đây:\n\na) Quyền sử dụng đất;\n\nb) Nhà ở."
    repealed_clause = "3. Các trường hợp:\n\na) (được bãi bỏ);\n\nb) (được bãi bỏ)."
    repealed = unit("LTEST_2024_D4_K3", "clause", article="4", clause="3", content=repealed_clause)
    repealed["provision_status"] = "repealed"
    repealed["is_retrievable"] = False
    doc["legal_units"] = [
        unit("LTEST_2024_D1", "article", clause=None, content="Điều không chia khoản."),
        unit("LTEST_2024_D2_K0", "article_lead", article="2", clause=None, content="Trong Điều này:"),
        unit("LTEST_2024_D2_K1", "clause", article="2", clause="1", content="1. Khoản không có điểm."),
        unit("LTEST_2024_D3_K2", "clause", article="3", clause="2", content=point_clause),
        repealed,
    ]
    result = build_chunks_for_document(doc, "LTEST_2024_normalized.json")
    return doc, result.chunks, result.report.to_dict()


def by_id(chunks: list[dict], chunk_id: str) -> dict:
    return next(chunk for chunk in chunks if chunk["chunk_id"] == chunk_id)


def test_article_creates_one_article_chunk() -> None:
    _, chunks, report = build_sample()

    article = by_id(chunks, "LTEST_2024_D1")
    assert article["unit_type"] == "article"
    assert article["payload"]["has_children"] is False
    assert report["article_chunks"] == 1


def test_article_lead_is_not_emitted() -> None:
    _, chunks, report = build_sample()

    assert "LTEST_2024_D2_K0" not in {chunk["chunk_id"] for chunk in chunks}
    assert report["article_leads_skipped"] == 1


def test_clause_without_point_creates_clause_chunk() -> None:
    _, chunks, _ = build_sample()

    clause = by_id(chunks, "LTEST_2024_D2_K1")
    assert clause["unit_type"] == "clause"
    assert clause["payload"]["has_children"] is False


def test_clause_with_points_creates_parent_and_children_in_order() -> None:
    _, chunks, _ = build_sample()
    ids = [chunk["chunk_id"] for chunk in chunks]
    parent_index = ids.index("LTEST_2024_D3_K2")

    assert ids[parent_index : parent_index + 3] == ["LTEST_2024_D3_K2", "LTEST_2024_D3_K2_DA", "LTEST_2024_D3_K2_DB"]


def test_parent_has_children_and_child_ids() -> None:
    _, chunks, _ = build_sample()
    parent = by_id(chunks, "LTEST_2024_D3_K2")

    assert parent["payload"]["has_children"] is True
    assert parent["payload"]["child_ids"] == ["LTEST_2024_D3_K2_DA", "LTEST_2024_D3_K2_DB"]


def test_child_has_parent_id() -> None:
    _, chunks, _ = build_sample()

    assert by_id(chunks, "LTEST_2024_D3_K2_DA")["payload"]["parent_id"] == "LTEST_2024_D3_K2"


def test_child_inherits_law_metadata_tags_and_cross_references() -> None:
    _, chunks, _ = build_sample()
    child = by_id(chunks, "LTEST_2024_D3_K2_DA")

    assert child["payload"]["law_id"] == "LTEST_2024"
    assert child["payload"]["law_name"] == "Luật Thử nghiệm 2024"
    assert child["payload"]["tags"] == ["đất đai"]
    assert child["payload"]["cross_references"][0]["anchor_text"] == "Điều 1"


def test_parent_with_points_is_not_retrievable() -> None:
    _, chunks, _ = build_sample()

    assert by_id(chunks, "LTEST_2024_D3_K2")["payload"]["is_retrievable"] is False


def test_effective_child_is_retrievable() -> None:
    _, chunks, _ = build_sample()

    assert by_id(chunks, "LTEST_2024_D3_K2_DA")["payload"]["is_retrievable"] is True


def test_repealed_child_is_not_retrievable() -> None:
    _, chunks, _ = build_sample()

    assert by_id(chunks, "LTEST_2024_D4_K3_DA")["payload"]["is_retrievable"] is False


def test_point_embedding_text_contains_expected_context_only() -> None:
    _, chunks, _ = build_sample()
    text = by_id(chunks, "LTEST_2024_D3_K2_DA")["embedding_text"]

    assert "Văn bản: Luật Thử nghiệm 2024" in text
    assert "Điều 3: Phạm vi điều chỉnh" in text
    assert "Khoản 2: Các trường hợp sau đây:" in text
    assert "Điểm a: Quyền sử dụng đất;" in text
    assert "Không được đưa vào embedding" not in text
    assert "b) Nhà ở" not in text


def test_chunk_ids_are_unique_and_report_counts_chunks() -> None:
    _, chunks, report = build_sample()
    ids = [chunk["chunk_id"] for chunk in chunks]

    assert len(ids) == len(set(ids))
    assert report["output_chunks"] == len(chunks)
    assert report["point_chunks"] == 4
    assert report["clauses_split"] == 2


def test_jsonl_output_has_one_chunk_per_line_and_unicode() -> None:
    _, chunks, _ = build_sample()
    temp_dir = Path("apps/api/tests/.tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    output = temp_dir / "chunks.jsonl"
    if output.exists():
        output.unlink()

    atomic_write_jsonl(output, chunks, overwrite=False)
    lines = output.read_text(encoding="utf-8").splitlines()

    assert len(lines) == len(chunks)
    assert all(json.loads(line) for line in lines)
    assert "Quyền sử dụng đất" in output.read_text(encoding="utf-8")
    output.unlink()

def test_normalized_input_is_not_mutated() -> None:
    doc = base_document()
    doc["legal_units"] = [unit("LTEST_2024_D3_K2", "clause", article="3", clause="2", content="2. Gồm:\n\na) A;\n\nb) B.")]
    before = deepcopy(doc)

    build_chunks_for_document(doc, "LTEST_2024_normalized.json")

    assert doc == before


def test_report_has_repealed_and_retrievable_counts() -> None:
    _, _, report = build_sample()

    assert report["repealed_chunks"] == 3
    assert report["retrievable_chunks"] > 0
    assert report["non_retrievable_chunks"] > 0
    assert report["error_count"] == 0


def test_invalid_point_sequence_stays_clause_and_warns() -> None:
    doc = base_document()
    doc["legal_units"] = [unit("LTEST_2024_D5_K1", "clause", article="5", clause="1", content="1. Gồm:\n\na) A;\n\nc) C;\n\nb) B.")]

    result = build_chunks_for_document(doc, "LTEST_2024_normalized.json")

    assert [chunk["chunk_id"] for chunk in result.chunks] == ["LTEST_2024_D5_K1"]
    assert result.report.to_dict()["warnings"][0]["code"] == "INVALID_POINT_SEQUENCE"



