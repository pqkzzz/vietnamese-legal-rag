from __future__ import annotations

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import LegalProvisionHierarchyIndex, ProvisionLevel


def _record(
    chunk_id: str,
    *,
    law_id: str = "LDD_2024",
    unit_type: str = "clause",
    article_number: str = "121",
    clause_number: str | None = None,
    point_number: str | None = None,
    parent_id: str | None = None,
    child_ids: list[str] | None = None,
    has_children: bool = False,
    content_clean: str | None = None,
    source_unit_id: str | None = None,
) -> dict[str, object]:
    payload = {
        "law_id": law_id,
        "law_name": "Luật Đất đai 2024" if law_id == "LDD_2024" else "Luật Khác",
        "chapter_number": "1",
        "chapter_title": "Chương test",
        "section_number": None,
        "section_title": None,
        "article_number": article_number,
        "article_title": "Chuyển mục đích sử dụng đất" if article_number == "121" else "Điều khác",
        "clause_number": clause_number,
        "point_number": point_number,
        "article_id": f"{law_id}_D{article_number}",
        "parent_id": parent_id,
        "content_raw": content_clean or f"Nội dung {chunk_id}",
        "content_clean": content_clean or f"Nội dung {chunk_id}",
        "clause_lead_raw": "1. Các trường hợp bao gồm:" if point_number else None,
        "clause_lead_clean": "1. Các trường hợp bao gồm:" if point_number else None,
        "has_children": has_children,
        "child_ids": child_ids or [],
        "cross_references": [
            {
                "reference_type": "internal",
                "target_law_id": law_id,
                "target_article_number": "122",
                "target_clause_number": None,
                "target_point_number": None,
                "target_unit_id": f"{law_id}_D122",
                "anchor_text": "Điều 122",
                "description_summary": "Điều khác",
                "raw_reference": {"target_id": f"{law_id}_D122"},
            }
        ] if chunk_id.endswith("DB") else [],
        "tags": ["test"],
        "provision_status": "effective",
        "is_retrievable": unit_type != "clause" or not has_children,
        "document_status": "effective",
        "source": {"source_file": "fixture.json", "source_url": None},
    }
    return {
        "chunk_id": chunk_id,
        "source_unit_id": source_unit_id or chunk_id,
        "unit_type": unit_type,
        "embedding_text": f"Embedding {chunk_id}",
        "payload": payload,
    }


def _write_jsonl(directory: Path, filename: str, records: list[dict[str, object]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records), encoding="utf-8")


def _fixture_index(tmp_path: Path) -> LegalProvisionHierarchyIndex:
    records = [
        _record("LDD_2024_D121", unit_type="article", clause_number=None, parent_id=None),
        _record(
            "LDD_2024_D121_K1",
            unit_type="clause",
            clause_number="1",
            parent_id="LDD_2024_D121",
            has_children=True,
            child_ids=["LDD_2024_D121_K1_DA", "LDD_2024_D121_K1_DB", "LDD_2024_D121_K1_DDD"],
            content_clean="1. Các trường hợp bao gồm:\n\na) A;\n\nb) B;\n\nđ) Đ;",
        ),
        _record("LDD_2024_D121_K1_DA", unit_type="point", clause_number="1", point_number="a", parent_id="LDD_2024_D121_K1", source_unit_id="LDD_2024_D121_K1"),
        _record("LDD_2024_D121_K1_DB", unit_type="point", clause_number="1", point_number="b", parent_id="LDD_2024_D121_K1", source_unit_id="LDD_2024_D121_K1", content_clean="b) Chuyển đất nông nghiệp sang đất phi nông nghiệp;"),
        _record("LDD_2024_D121_K1_DDD", unit_type="point", clause_number="1", point_number="đ", parent_id="LDD_2024_D121_K1", source_unit_id="LDD_2024_D121_K1"),
        _record("LDD_2024_D121_K2", unit_type="clause", clause_number="2", parent_id="LDD_2024_D121"),
        _record("LDD_2024_D122_K1", unit_type="clause", article_number="122", clause_number="1", parent_id="LDD_2024_D122"),
        _record("OTHER_2024_D121_K1", law_id="OTHER_2024", unit_type="clause", article_number="121", clause_number="1", parent_id="OTHER_2024_D121"),
        _record("LDD_2024_D123_K1_DA", unit_type="point", article_number="123", clause_number="1", point_number="a", parent_id="LDD_2024_D123_K1"),
    ]
    _write_jsonl(tmp_path, "LDD_2024_chunks.jsonl", records)
    return LegalProvisionHierarchyIndex.from_jsonl_directory(tmp_path)


def test_build_index_from_jsonl_directory(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    report = index.get_build_report()
    assert report.total_records == 9
    assert report.total_nodes == 9
    assert report.article_nodes == 1
    assert report.clause_nodes == 4
    assert report.point_nodes == 4


def test_get_node_returns_expected_node(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    node = index.get_node("LDD_2024_D121_K1_DB")
    assert node is not None
    assert node.chunk_id == "LDD_2024_D121_K1_DB"
    assert node.level == ProvisionLevel.POINT


def test_point_b_has_parent_clause(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    parent = index.get_parent("LDD_2024_D121_K1_DB")
    assert parent is not None
    assert parent.chunk_id == "LDD_2024_D121_K1"


def test_parent_clause_returns_children_in_declared_order(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    children = index.get_children("LDD_2024_D121_K1")
    assert [node.chunk_id for node in children] == [
        "LDD_2024_D121_K1_DA",
        "LDD_2024_D121_K1_DB",
        "LDD_2024_D121_K1_DDD",
    ]


def test_point_siblings_share_parent_and_exclude_self(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    siblings = index.get_siblings("LDD_2024_D121_K1_DB")
    assert [node.chunk_id for node in siblings] == ["LDD_2024_D121_K1_DA", "LDD_2024_D121_K1_DDD"]
    assert all(node.parent_id == "LDD_2024_D121_K1" for node in siblings)


def test_previous_and_next_sibling_follow_file_order(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    previous_node = index.get_previous_sibling("LDD_2024_D121_K1_DB")
    next_node = index.get_next_sibling("LDD_2024_D121_K1_DB")
    assert previous_node is not None and previous_node.chunk_id == "LDD_2024_D121_K1_DA"
    assert next_node is not None and next_node.chunk_id == "LDD_2024_D121_K1_DDD"


def test_clause_without_real_article_parent_returns_none(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    assert index.get_node("LDD_2024_D122") is None
    assert index.get_parent("LDD_2024_D122_K1") is None


def test_lookup_point_returns_exact_point_only(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    result = index.lookup("LDD_2024", "121", "1", "b")
    assert result.found is True
    assert result.matched_level == ProvisionLevel.POINT
    assert result.exact_node is not None
    assert result.exact_node.chunk_id == "LDD_2024_D121_K1_DB"
    assert [node.chunk_id for node in result.nodes] == ["LDD_2024_D121_K1_DB"]


def test_lookup_clause_returns_parent_and_point_children(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    result = index.lookup("LDD_2024", "121", "1")
    assert result.found is True
    assert result.matched_level == ProvisionLevel.CLAUSE
    assert [node.chunk_id for node in result.nodes] == [
        "LDD_2024_D121_K1",
        "LDD_2024_D121_K1_DA",
        "LDD_2024_D121_K1_DB",
        "LDD_2024_D121_K1_DDD",
    ]


def test_lookup_article_returns_all_nodes_for_article(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    result = index.lookup("LDD_2024", "121")
    assert result.found is True
    assert [node.chunk_id for node in result.nodes] == [
        "LDD_2024_D121",
        "LDD_2024_D121_K1",
        "LDD_2024_D121_K1_DA",
        "LDD_2024_D121_K1_DB",
        "LDD_2024_D121_K1_DDD",
        "LDD_2024_D121_K2",
    ]


def test_lookup_not_found_returns_structured_result(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    result = index.lookup("LDD_2024", "999")
    assert result.found is False
    assert result.nodes == []
    assert result.exact_node is None
    assert result.matched_level is None


def test_lookup_does_not_cross_laws(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    result = index.lookup("LDD_2024", "121", "1")
    assert all(node.law_id == "LDD_2024" for node in result.nodes)
    other = index.lookup("OTHER_2024", "121", "1")
    assert [node.chunk_id for node in other.nodes] == ["OTHER_2024_D121_K1"]


def test_orphan_does_not_crash_and_warns(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    assert index.get_node("LDD_2024_D123_K1_DA") is not None
    assert any(warning.code == "ORPHAN_PARENT" for warning in index.warnings)


def test_duplicate_chunk_id_is_detected(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        "LDD_2024_chunks.jsonl",
        [
            _record("LDD_2024_D121", unit_type="article"),
            _record("LDD_2024_D121", unit_type="article", content_clean="Duplicate"),
        ],
    )
    index = LegalProvisionHierarchyIndex.from_jsonl_directory(tmp_path)
    assert index.get_build_report().duplicate_chunk_ids == 1
    assert any(warning.code == "DUPLICATE_CHUNK_ID" for warning in index.warnings)


def test_duplicate_legal_location_is_detected(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        "LDD_2024_chunks.jsonl",
        [
            _record("LDD_2024_D121_K1_DA", unit_type="point", clause_number="1", point_number="a", parent_id="LDD_2024_D121_K1"),
            _record("LDD_2024_D121_K1_DA_COPY", unit_type="point", clause_number="1", point_number="a", parent_id="LDD_2024_D121_K1"),
        ],
    )
    index = LegalProvisionHierarchyIndex.from_jsonl_directory(tmp_path)
    assert index.get_build_report().duplicate_locations == 1
    assert any(warning.code == "DUPLICATE_LOCATION" for warning in index.warnings)


def test_parent_child_mismatch_is_detected(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        "LDD_2024_chunks.jsonl",
        [
            _record("LDD_2024_D121_K1", unit_type="clause", clause_number="1", has_children=True, child_ids=["LDD_2024_D121_K1_DA"]),
            _record("LDD_2024_D121_K1_DA", unit_type="point", clause_number="1", point_number="a", parent_id="WRONG_PARENT"),
        ],
    )
    index = LegalProvisionHierarchyIndex.from_jsonl_directory(tmp_path)
    assert any(warning.code == "PARENT_CHILD_MISMATCH" for warning in index.warnings)


def test_non_retrievable_parent_clause_stays_in_hierarchy(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    node = index.get_node("LDD_2024_D121_K1")
    assert node is not None
    assert node.is_retrievable is False
    assert node in index.lookup("LDD_2024", "121", "1").nodes


def test_raw_metadata_clause_lead_and_cross_references_are_preserved(tmp_path: Path) -> None:
    index = _fixture_index(tmp_path)
    node = index.get_node("LDD_2024_D121_K1_DB")
    assert node is not None
    assert node.clause_lead_clean == "1. Các trường hợp bao gồm:"
    assert node.cross_references[0]["target_unit_id"] == "LDD_2024_D122"
    assert node.metadata["payload"]["content_clean"] == "b) Chuyển đất nông nghiệp sang đất phi nông nghiệp;"
