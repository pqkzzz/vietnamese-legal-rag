from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.evidence import (
    DependencyReason,
    LegalDependencyDetector,
    LegalReference,
    LegalReferenceType,
    ProvisionLevel,
    ProvisionNode,
)


class FakeHierarchy:
    def __init__(self, nodes: list[ProvisionNode]) -> None:
        self.nodes = {node.chunk_id: node for node in nodes}

    def get_node(self, chunk_id: str) -> ProvisionNode | None:
        return self.nodes.get(chunk_id)

    def get_parent(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or node.parent_id is None:
            return None
        return self.get_node(node.parent_id)

    def get_children(self, chunk_id: str) -> list[ProvisionNode]:
        node = self.get_node(chunk_id)
        if node is None:
            return []
        declared = [self.nodes[child_id] for child_id in node.child_ids if child_id in self.nodes]
        by_parent = [child for child in self.nodes.values() if child.parent_id == chunk_id and child not in declared]
        return declared + sorted(by_parent, key=lambda item: item.order_index)

    def get_siblings(self, chunk_id: str) -> list[ProvisionNode]:
        node = self.get_node(chunk_id)
        if node is None or node.parent_id is None:
            return []
        return [child for child in self.get_children(node.parent_id) if child.chunk_id != chunk_id]

    def get_previous_sibling(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or node.previous_sibling_id is None:
            return None
        return self.get_node(node.previous_sibling_id)

    def get_next_sibling(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or node.next_sibling_id is None:
            return None
        return self.get_node(node.next_sibling_id)


def _node(
    chunk_id: str = "LAW_D1_K1",
    *,
    level: ProvisionLevel = ProvisionLevel.CLAUSE,
    content: str = "Nội dung hoàn chỉnh.",
    clause_lead: str | None = None,
    parent_id: str | None = "LAW_D1",
    child_ids: tuple[str, ...] = (),
    has_children: bool = False,
    cross_references: list[dict[str, object]] | None = None,
    article_number: str | None = "1",
    clause_number: str | None = "1",
    point_number: str | None = None,
    previous_sibling_id: str | None = None,
    next_sibling_id: str | None = None,
    order_index: int = 0,
) -> ProvisionNode:
    return ProvisionNode(
        qdrant_point_id=None,
        chunk_id=chunk_id,
        source_unit_id=chunk_id,
        unit_type=level.value,
        level=level,
        law_id="LAW",
        law_name="Luật test",
        chapter_number=None,
        chapter_title=None,
        section_number=None,
        section_title=None,
        article_number=article_number,
        article_title="Điều test",
        clause_number=clause_number,
        point_number=point_number,
        article_id=f"LAW_D{article_number}" if article_number else None,
        parent_id=parent_id,
        child_ids=child_ids,
        has_children=has_children,
        content_raw=content,
        content_clean=content,
        clause_lead_raw=clause_lead,
        clause_lead_clean=clause_lead,
        cross_references=cross_references or [],
        tags=[],
        provision_status="effective",
        is_retrievable=True,
        document_status="effective",
        order_index=order_index,
        previous_sibling_id=previous_sibling_id,
        next_sibling_id=next_sibling_id,
        metadata={},
    )


def _point(chunk_id: str = "LAW_D1_K1_DA", **kwargs: object) -> ProvisionNode:
    defaults = {
        "level": ProvisionLevel.POINT,
        "content": "a) Mục danh sách;",
        "parent_id": "LAW_D1_K1",
        "article_number": "1",
        "clause_number": "1",
        "point_number": "a",
    }
    defaults.update(kwargs)
    return _node(chunk_id, **defaults)


def _reference(reference_type: LegalReferenceType) -> LegalReference:
    return LegalReference(
        source_chunk_id="LAW_D1_K1",
        reference_type=reference_type,
        target_law_id="LAW",
        target_article_number="1",
        target_clause_number=None,
        target_point_number=None,
        target_unit_id=None,
        anchor_text="Điều này",
        description_summary=None,
        raw_text="Điều này",
        confidence=0.8,
        parser_source="test",
        metadata={},
    )


def test_point_with_clause_lead_needs_parent() -> None:
    point = _point(clause_lead="1. Các trường hợp bao gồm:")

    signal = LegalDependencyDetector().detect(point)

    assert signal.needs_parent is True
    assert signal.is_self_contained is False
    assert DependencyReason.POINT_REQUIRES_PARENT in signal.reasons
    assert DependencyReason.POINT_HAS_CLAUSE_LEAD in signal.reasons


def test_point_in_list_parent_with_multiple_children_needs_siblings() -> None:
    parent = _node(
        "LAW_D1_K1",
        content="Các trường hợp chuyển mục đích sử dụng đất bao gồm:",
        child_ids=("LAW_D1_K1_DA", "LAW_D1_K1_DB"),
        has_children=True,
    )
    point_a = _point("LAW_D1_K1_DA", point_number="a", order_index=1)
    point_b = _point("LAW_D1_K1_DB", point_number="b", order_index=2)
    hierarchy = FakeHierarchy([parent, point_a, point_b])

    signal = LegalDependencyDetector().detect(point_b, hierarchy=hierarchy)

    assert signal.needs_parent is True
    assert signal.needs_siblings is True
    assert DependencyReason.LIST_INTRODUCTION in signal.reasons


def test_point_with_siblings_but_parent_has_no_list_marker_does_not_need_siblings() -> None:
    parent = _node("LAW_D1_K1", content="Cha không có marker danh sách.", child_ids=("LAW_D1_K1_DA", "LAW_D1_K1_DB"), has_children=True)
    point_a = _point("LAW_D1_K1_DA", point_number="a", order_index=1)
    point_b = _point("LAW_D1_K1_DB", point_number="b", order_index=2)
    hierarchy = FakeHierarchy([parent, point_a, point_b])

    signal = LegalDependencyDetector().detect(point_b, hierarchy=hierarchy)

    assert signal.needs_parent is True
    assert signal.needs_siblings is False


def test_parent_clause_with_child_ids_needs_children() -> None:
    clause = _node("LAW_D1_K1", content="Nội dung cha.", child_ids=("LAW_D1_K1_DA",), has_children=True)

    signal = LegalDependencyDetector().detect(clause)

    assert signal.needs_children is True
    assert DependencyReason.PARENT_HAS_CHILDREN in signal.reasons


def test_parent_clause_with_bao_gom_marker_adds_list_introduction() -> None:
    clause = _node("LAW_D1_K1", content="Các trường hợp bao gồm:", child_ids=("LAW_D1_K1_DA",), has_children=True)

    signal = LegalDependencyDetector().detect(clause)

    assert signal.needs_children is True
    assert DependencyReason.LIST_INTRODUCTION in signal.reasons
    assert "bao gồm" in signal.matched_markers


def test_plain_complete_clause_is_self_contained() -> None:
    clause = _node("LAW_D1_K2", content="Người sử dụng đất được thực hiện quyền theo quy định của pháp luật.", parent_id="LAW_D1")

    signal = LegalDependencyDetector().detect(clause)

    assert signal.is_self_contained is True
    assert all(
        value is False
        for value in (
            signal.needs_parent,
            signal.needs_children,
            signal.needs_siblings,
            signal.needs_previous_neighbor,
            signal.needs_next_neighbor,
            signal.needs_references,
        )
    )
    assert DependencyReason.SELF_CONTAINED in signal.reasons


def test_clause_with_virtual_article_parent_does_not_need_parent() -> None:
    clause = _node("LAW_D1_K1", content="Khoản này hoàn chỉnh.", parent_id="LAW_D1")

    signal = LegalDependencyDetector().detect(clause, hierarchy=FakeHierarchy([clause]))

    assert signal.needs_parent is False
    assert signal.metadata["parent_available"] is False


def test_structured_cross_references_need_references() -> None:
    clause = _node("LAW_D1_K1", cross_references=[{"target_unit_id": "LAW_D2"}])

    signal = LegalDependencyDetector().detect(clause)

    assert signal.needs_references is True
    assert DependencyReason.DIRECT_LEGAL_REFERENCE in signal.reasons


def test_relative_parsed_reference_needs_references() -> None:
    clause = _node("LAW_D1_K1")

    signal = LegalDependencyDetector().detect(clause, parsed_references=[_reference(LegalReferenceType.RELATIVE)])

    assert signal.needs_references is True
    assert DependencyReason.RELATIVE_LEGAL_REFERENCE in signal.reasons


def test_content_reference_marker_needs_references() -> None:
    clause = _node("LAW_D1_K1", content="Thực hiện theo quy định tại Điều 34 của Luật này.")

    signal = LegalDependencyDetector().detect(clause)

    assert signal.needs_references is True
    assert DependencyReason.DIRECT_LEGAL_REFERENCE in signal.reasons


def test_dieu_kien_is_not_reference_marker() -> None:
    clause = _node("LAW_D1_K1", content="Điều kiện chuyển nhượng được quy định rõ ràng.")

    signal = LegalDependencyDetector().detect(clause)

    assert signal.needs_references is False


def test_exception_marker_does_not_imply_sibling_or_neighbor() -> None:
    clause = _node("LAW_D1_K1", content="Trừ trường hợp pháp luật có quy định khác, quyền này được thực hiện.")

    signal = LegalDependencyDetector().detect(clause)

    assert DependencyReason.EXCEPTION_MARKER in signal.reasons
    assert signal.needs_siblings is False
    assert signal.needs_previous_neighbor is False
    assert signal.needs_next_neighbor is False


def test_backward_marker_with_previous_sibling_needs_previous_neighbor() -> None:
    previous = _node("LAW_D1_K1", order_index=1)
    current = _node("LAW_D1_K2", content="Theo khoản liền trước, hồ sơ được xử lý.", previous_sibling_id="LAW_D1_K1", order_index=2)
    hierarchy = FakeHierarchy([previous, current])

    signal = LegalDependencyDetector().detect(current, hierarchy=hierarchy)

    assert signal.needs_previous_neighbor is True
    assert DependencyReason.BACKWARD_DEPENDENCY in signal.reasons


def test_forward_marker_with_next_sibling_needs_next_neighbor() -> None:
    current = _node("LAW_D1_K1", content="Theo khoản liền sau, hồ sơ được bổ sung.", next_sibling_id="LAW_D1_K2", order_index=1)
    next_node = _node("LAW_D1_K2", order_index=2)
    hierarchy = FakeHierarchy([current, next_node])

    signal = LegalDependencyDetector().detect(current, hierarchy=hierarchy)

    assert signal.needs_next_neighbor is True
    assert DependencyReason.FORWARD_DEPENDENCY in signal.reasons


def test_cac_truong_hop_sau_day_is_list_not_next_neighbor() -> None:
    clause = _node("LAW_D1_K1", content="Các trường hợp sau đây:", child_ids=("LAW_D1_K1_DA",), has_children=True)
    child = _point("LAW_D1_K1_DA")
    hierarchy = FakeHierarchy([clause, child])

    signal = LegalDependencyDetector().detect(clause, hierarchy=hierarchy)

    assert signal.needs_children is True
    assert DependencyReason.LIST_INTRODUCTION in signal.reasons
    assert signal.needs_next_neighbor is False


def test_orphan_point_does_not_crash_and_records_parent_unavailable() -> None:
    point = _point("LAW_D1_K1_DA", content="a) Chuyển đất nông nghiệp sang đất phi nông nghiệp;", parent_id="LAW_D1_K1")

    signal = LegalDependencyDetector().detect(point, hierarchy=FakeHierarchy([point]))

    assert signal.needs_parent is True
    assert signal.metadata["parent_available"] is False


def test_detect_many_preserves_input_order() -> None:
    first = _node("LAW_D1_K1")
    second = _node("LAW_D1_K2")

    signals = LegalDependencyDetector().detect_many([first, second])

    assert [signal.source_chunk_id for signal in signals] == ["LAW_D1_K1", "LAW_D1_K2"]


def test_confidence_is_clamped() -> None:
    point = _point(
        "LAW_D1_K1_DA",
        content="a) Nội dung; trừ trường hợp theo khoản liền trước và theo khoản liền sau.",
        clause_lead="Các trường hợp bao gồm:",
        previous_sibling_id="LAW_D1_K1_D0",
        next_sibling_id="LAW_D1_K1_DB",
    )
    previous = _point("LAW_D1_K1_D0", point_number="0")
    next_node = _point("LAW_D1_K1_DB", point_number="b")
    parent = _node("LAW_D1_K1", content="Các trường hợp bao gồm:", child_ids=("LAW_D1_K1_D0", "LAW_D1_K1_DA", "LAW_D1_K1_DB"), has_children=True)

    signal = LegalDependencyDetector().detect(point, hierarchy=FakeHierarchy([parent, previous, point, next_node]))

    assert 0.0 <= signal.confidence <= 1.0


def test_reasons_are_deduplicated() -> None:
    clause = _node(
        "LAW_D1_K1",
        content="Theo quy định tại Điều 34 và theo quy định tại Điều 35.",
        cross_references=[{"target_unit_id": "LAW_D34"}],
    )

    signal = LegalDependencyDetector().detect(clause, parsed_references=[_reference(LegalReferenceType.INTERNAL)])

    assert len(signal.reasons) == len(set(signal.reasons))


def test_self_contained_never_conflicts_with_needs_flags() -> None:
    detector = LegalDependencyDetector()
    signals = [
        detector.detect(_node("LAW_D1_K1")),
        detector.detect(_node("LAW_D1_K2", cross_references=[{"target_unit_id": "LAW_D2"}])),
        detector.detect(_point("LAW_D1_K1_DA")),
    ]

    for signal in signals:
        if signal.is_self_contained:
            assert not any(
                (
                    signal.needs_parent,
                    signal.needs_children,
                    signal.needs_siblings,
                    signal.needs_previous_neighbor,
                    signal.needs_next_neighbor,
                    signal.needs_references,
                )
            )
