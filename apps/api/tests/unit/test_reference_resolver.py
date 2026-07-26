from __future__ import annotations

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import (
    LegalProvisionHierarchyIndex,
    LegalReference,
    LegalReferenceParser,
    LegalReferenceResolver,
    LegalReferenceType,
    ReferenceResolutionStatus,
)


def _record(
    chunk_id: str,
    *,
    law_id: str = "LAW",
    unit_type: str = "clause",
    article_number: str = "10",
    clause_number: str | None = None,
    point_number: str | None = None,
    parent_id: str | None = None,
    child_ids: list[str] | None = None,
    has_children: bool = False,
    content_clean: str | None = None,
    cross_references: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "chunk_id": chunk_id,
        "source_unit_id": parent_id if unit_type == "point" and parent_id else chunk_id,
        "unit_type": unit_type,
        "embedding_text": f"Embedding {chunk_id}",
        "payload": {
            "law_id": law_id,
            "law_name": "Luật test",
            "chapter_number": None,
            "chapter_title": None,
            "section_number": None,
            "section_title": None,
            "article_number": article_number,
            "article_title": f"Điều {article_number}",
            "clause_number": clause_number,
            "point_number": point_number,
            "article_id": f"{law_id}_D{article_number}",
            "parent_id": parent_id,
            "content_raw": content_clean or f"Nội dung {chunk_id}",
            "content_clean": content_clean or f"Nội dung {chunk_id}",
            "clause_lead_raw": "1. Lead" if point_number else None,
            "clause_lead_clean": "1. Lead" if point_number else None,
            "has_children": has_children,
            "child_ids": child_ids or [],
            "cross_references": cross_references or [],
            "tags": [],
            "provision_status": "effective",
            "is_retrievable": unit_type != "clause" or not has_children,
            "document_status": "effective",
            "source": {"source_file": "fixture.json", "source_url": None},
        },
    }


def _write_jsonl(directory: Path, records: list[dict[str, object]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "fixture_chunks.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        encoding="utf-8",
    )


def _hierarchy(tmp_path: Path) -> LegalProvisionHierarchyIndex:
    records = [
        _record("LAW_D10", unit_type="article", article_number="10"),
        _record(
            "LAW_D10_K1",
            unit_type="clause",
            article_number="10",
            clause_number="1",
            parent_id="LAW_D10",
            has_children=True,
            child_ids=["LAW_D10_K1_DA", "LAW_D10_K1_DB"],
            content_clean="1. Lead a) A; b) B;",
        ),
        _record("LAW_D10_K1_DA", unit_type="point", article_number="10", clause_number="1", point_number="a", parent_id="LAW_D10_K1"),
        _record("LAW_D10_K1_DB", unit_type="point", article_number="10", clause_number="1", point_number="b", parent_id="LAW_D10_K1"),
        _record("LAW_D10_K2", unit_type="clause", article_number="10", clause_number="2", parent_id="LAW_D10"),
        _record("LAW_D20_K1", unit_type="clause", article_number="20", clause_number="1", parent_id="LAW_D20"),
        _record("OTHER_D5", law_id="OTHER", unit_type="article", article_number="5"),
        _record("OTHER_D5_K1", law_id="OTHER", unit_type="clause", article_number="5", clause_number="1", parent_id="OTHER_D5"),
        _record(
            "LAW_D30_K1",
            unit_type="clause",
            article_number="30",
            clause_number="1",
            parent_id="LAW_D30",
            content_clean="Theo Điều 999 và Điều 10.",
            cross_references=[
                {"reference_type": "internal", "target_law_id": "LAW", "target_article_number": "10", "anchor_text": "Điều 10"},
                {"reference_type": "internal", "target_law_id": "LAW", "target_article_number": "999", "anchor_text": "Điều 999"},
            ],
        ),
    ]
    _write_jsonl(tmp_path, records)
    return LegalProvisionHierarchyIndex.from_jsonl_directory(tmp_path)


def _ref(
    source_chunk_id: str = "LAW_D30_K1",
    *,
    reference_type: LegalReferenceType = LegalReferenceType.INTERNAL,
    law_id: str | None = "LAW",
    article: str | None = None,
    clause: str | None = None,
    point: str | None = None,
    unit_id: str | None = None,
) -> LegalReference:
    return LegalReference(
        source_chunk_id=source_chunk_id,
        reference_type=reference_type,
        target_law_id=law_id,
        target_article_number=article,
        target_clause_number=clause,
        target_point_number=point,
        target_unit_id=unit_id,
        anchor_text=None,
        description_summary=None,
        raw_text=None,
        confidence=1.0,
        parser_source="test",
        metadata={},
    )


def test_resolve_existing_target_unit_id(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(unit_id="LAW_D10_K1_DB"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert resolved.exact_node is not None
    assert resolved.exact_node.chunk_id == "LAW_D10_K1_DB"


def test_resolve_point_location(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="10", clause="1", point="b"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["LAW_D10_K1_DB"]


def test_resolve_clause_location_as_exact_legal_scope(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="10", clause="1"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["LAW_D10_K1", "LAW_D10_K1_DA", "LAW_D10_K1_DB"]


def test_resolve_article_location_to_multiple_chunks(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="10"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == [
        "LAW_D10",
        "LAW_D10_K1",
        "LAW_D10_K1_DA",
        "LAW_D10_K1_DB",
        "LAW_D10_K2",
    ]


def test_resolve_article_container_without_article_chunk(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="20", unit_id="LAW_D20"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert resolved.exact_node is None
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["LAW_D20_K1"]


def test_resolve_relative_article_this(tmp_path: Path) -> None:
    hierarchy = _hierarchy(tmp_path)
    source = hierarchy.get_node("LAW_D30_K1")
    assert source is not None
    reference = LegalReferenceParser().parse_text(source, "Điều này")[0]
    resolved = LegalReferenceResolver(hierarchy).resolve(reference)
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["LAW_D30_K1"]


def test_resolve_relative_clause_this_article(tmp_path: Path) -> None:
    hierarchy = _hierarchy(tmp_path)
    source = hierarchy.get_node("LAW_D10_K2")
    assert source is not None
    reference = LegalReferenceParser().parse_text(source, "khoản 1 Điều này")[0]
    resolved = LegalReferenceResolver(hierarchy).resolve(reference)
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["LAW_D10_K1", "LAW_D10_K1_DA", "LAW_D10_K1_DB"]


def test_resolve_cross_law_when_target_law_is_clear(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(law_id="OTHER", article="5", clause="1"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert [node.chunk_id for node in resolved.resolved_nodes] == ["OTHER_D5_K1"]


def test_external_reference_missing_law_is_not_guessed(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(reference_type=LegalReferenceType.EXTERNAL, law_id=None, article="5"))
    assert resolved.status == ReferenceResolutionStatus.UNRESOLVED
    assert resolved.resolved_nodes == []


def test_missing_target_returns_unresolved(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="999"))
    assert resolved.status == ReferenceResolutionStatus.UNRESOLVED
    assert resolved.exact_node is None


def test_target_unit_id_location_conflict_has_warning(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="20", unit_id="LAW_D10_K1"))
    assert resolved.status == ReferenceResolutionStatus.RESOLVED_EXACT
    assert resolved.warnings


def test_resolved_nodes_stay_inside_target_law_and_article(tmp_path: Path) -> None:
    resolver = LegalReferenceResolver(_hierarchy(tmp_path))
    resolved = resolver.resolve(_ref(article="10"))
    assert all(node.law_id == "LAW" and node.article_number == "10" for node in resolved.resolved_nodes)


def test_resolver_does_not_create_fake_article_node(tmp_path: Path) -> None:
    hierarchy = _hierarchy(tmp_path)
    resolver = LegalReferenceResolver(hierarchy)
    resolved = resolver.resolve(_ref(article="20", unit_id="LAW_D20"))
    assert hierarchy.get_node("LAW_D20") is None
    assert resolved.exact_node is None


def test_resolve_node_counts_statuses(tmp_path: Path) -> None:
    hierarchy = _hierarchy(tmp_path)
    node = hierarchy.get_node("LAW_D30_K1")
    assert node is not None
    batch = LegalReferenceResolver(hierarchy).resolve_node(node)
    assert batch.resolved_count == 1
    assert batch.unresolved_count == 1
    assert batch.ambiguous_count == 0
