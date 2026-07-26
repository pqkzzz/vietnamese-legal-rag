"""Rule-based dependency signals for legal provision chunks."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.modules.evidence.hierarchy_index import LegalProvisionHierarchyIndex
from app.modules.evidence.models import (
    DependencyReason,
    DependencySignal,
    LegalReference,
    LegalReferenceType,
    ProvisionLevel,
    ProvisionNode,
)

SHORT_LIST_ITEM_MAX_CHARS = 120
BASE_CONFIDENCE = 0.35
SELF_CONTAINED_CONFIDENCE = 0.78

POINT_MARKER_RE = re.compile(r"^\s*[a-zđ]\)", re.IGNORECASE)
SENTENCE_END_RE = re.compile(r"[.!?;。…]$|\.$")

LIST_INTRODUCTION_MARKERS = (
    "bao gồm",
    "gồm",
    "các trường hợp sau đây",
    "được quy định như sau",
    "như sau",
    "cụ thể",
    "sau đây",
)

REFERENCE_MARKERS = (
    "theo quy định tại",
    "quy định tại điều",
    "quy định tại khoản",
    "quy định tại điểm",
    "theo điều",
    "theo khoản",
    "theo điểm",
    "điều này",
    "khoản này",
)

EXCEPTION_MARKERS = (
    "trừ trường hợp",
    "trừ các trường hợp",
    "ngoại trừ",
    "ngoài các trường hợp",
    "không áp dụng đối với",
    "trừ khi",
)

BACKWARD_MARKERS = (
    "quy định tại khoản trước",
    "theo khoản liền trước",
    "nêu tại khoản trên",
    "trường hợp quy định ở trên",
    "quy định tại điểm trước",
)

FORWARD_MARKERS = (
    "quy định tại khoản sau",
    "theo khoản liền sau",
    "nêu tại khoản dưới",
)

PROCEDURAL_MARKERS = (
    "bước tiếp theo",
    "sau khi",
    "trước khi",
    "tiếp theo",
    "thứ nhất",
    "thứ hai",
    "trình tự",
    "thủ tục",
)


class LegalDependencyDetector:
    """Detect query-independent context dependencies for provision nodes."""

    def detect(
        self,
        node: ProvisionNode,
        *,
        hierarchy: LegalProvisionHierarchyIndex | None = None,
        parsed_references: list[LegalReference] | None = None,
    ) -> DependencySignal:
        references = parsed_references or []
        reasons: list[DependencyReason] = []
        matched_markers: list[str] = []
        metadata: dict[str, Any] = {
            "level": node.level.value,
            "content_length": len(node.content_clean.strip()),
            "parsed_reference_count": len(references),
            "cross_reference_count": len(node.cross_references),
            "is_retrievable": node.is_retrievable,
        }

        parent = hierarchy.get_parent(node.chunk_id) if hierarchy is not None else None
        children = hierarchy.get_children(node.chunk_id) if hierarchy is not None else []
        siblings = hierarchy.get_siblings(node.chunk_id) if hierarchy is not None else []
        previous_sibling = hierarchy.get_previous_sibling(node.chunk_id) if hierarchy is not None else None
        next_sibling = hierarchy.get_next_sibling(node.chunk_id) if hierarchy is not None else None

        parent_available = parent is not None
        child_count = len(children) if hierarchy is not None else len(node.child_ids)
        sibling_count = len(siblings)
        previous_available = previous_sibling is not None
        next_available = next_sibling is not None

        metadata.update(
            {
                "parent_available": parent_available,
                "child_count": child_count,
                "sibling_count": sibling_count,
                "previous_available": previous_available,
                "next_available": next_available,
            }
        )

        content = node.content_clean or ""
        lead = node.clause_lead_clean or ""
        combined_text = "\n".join(part for part in (lead, content) if part)

        needs_parent = False
        needs_children = False
        needs_siblings = False
        needs_previous_neighbor = False
        needs_next_neighbor = False
        needs_references = False

        list_markers = _find_markers(combined_text, LIST_INTRODUCTION_MARKERS)
        reference_markers = _find_markers(content, REFERENCE_MARKERS)
        exception_markers = _find_markers(content, EXCEPTION_MARKERS)
        backward_markers = _find_markers(content, BACKWARD_MARKERS)
        forward_markers = _find_markers(content, FORWARD_MARKERS)
        procedural_markers = _find_markers(content, PROCEDURAL_MARKERS)

        for marker in exception_markers:
            _add_marker(matched_markers, marker)
        if exception_markers:
            _add_reason(reasons, DependencyReason.EXCEPTION_MARKER)

        for marker in procedural_markers:
            _add_marker(matched_markers, marker)
        if procedural_markers:
            _add_reason(reasons, DependencyReason.PROCEDURAL_SEQUENCE)

        if _is_incomplete_content(content) or list_markers:
            _add_reason(reasons, DependencyReason.INCOMPLETE_SENTENCE)

        if node.level == ProvisionLevel.POINT:
            needs_parent = self._point_needs_parent(node, parent_available)
            if needs_parent:
                _add_reason(reasons, DependencyReason.POINT_REQUIRES_PARENT)
            if _has_text(lead):
                _add_reason(reasons, DependencyReason.POINT_HAS_CLAUSE_LEAD)
            if _is_short_list_item(node):
                _add_reason(reasons, DependencyReason.SHORT_LIST_ITEM)
            if parent is not None and (parent.has_children or child_count > 0 or len(_point_children(hierarchy, parent)) > 1):
                _add_reason(reasons, DependencyReason.PARENT_HAS_CHILDREN)
            if self._point_needs_siblings(node, parent, hierarchy):
                needs_siblings = True
                _add_reason(reasons, DependencyReason.PARENT_HAS_CHILDREN)
                _add_reason(reasons, DependencyReason.LIST_INTRODUCTION)
                for marker in _find_markers(_parent_context(parent), LIST_INTRODUCTION_MARKERS):
                    _add_marker(matched_markers, marker)

        elif node.level == ProvisionLevel.CLAUSE:
            if node.has_children and (node.child_ids or child_count > 0):
                needs_children = True
                _add_reason(reasons, DependencyReason.PARENT_HAS_CHILDREN)
            if needs_children and list_markers:
                _add_reason(reasons, DependencyReason.LIST_INTRODUCTION)
                for marker in list_markers:
                    _add_marker(matched_markers, marker)

        elif node.level == ProvisionLevel.ARTICLE:
            if child_count > 0 and list_markers:
                needs_children = True
                _add_reason(reasons, DependencyReason.PARENT_HAS_CHILDREN)
                _add_reason(reasons, DependencyReason.LIST_INTRODUCTION)
                for marker in list_markers:
                    _add_marker(matched_markers, marker)

        if node.cross_references or references or reference_markers:
            needs_references = True
            for marker in reference_markers:
                _add_marker(matched_markers, marker)
            if any(reference.reference_type == LegalReferenceType.RELATIVE for reference in references):
                _add_reason(reasons, DependencyReason.RELATIVE_LEGAL_REFERENCE)
            if node.cross_references or any(reference.reference_type != LegalReferenceType.RELATIVE for reference in references) or reference_markers:
                _add_reason(reasons, DependencyReason.DIRECT_LEGAL_REFERENCE)

        if backward_markers:
            _add_reason(reasons, DependencyReason.BACKWARD_DEPENDENCY)
            for marker in backward_markers:
                _add_marker(matched_markers, marker)
            needs_previous_neighbor = previous_available

        if forward_markers:
            _add_reason(reasons, DependencyReason.FORWARD_DEPENDENCY)
            for marker in forward_markers:
                _add_marker(matched_markers, marker)
            needs_next_neighbor = next_available

        if list_markers and node.level != ProvisionLevel.POINT:
            for marker in list_markers:
                _add_marker(matched_markers, marker)

        any_need = any(
            (
                needs_parent,
                needs_children,
                needs_siblings,
                needs_previous_neighbor,
                needs_next_neighbor,
                needs_references,
            )
        )
        dependency_marker_present = any(
            reason
            for reason in reasons
            if reason
            in {
                DependencyReason.EXCEPTION_MARKER,
                DependencyReason.FORWARD_DEPENDENCY,
                DependencyReason.BACKWARD_DEPENDENCY,
                DependencyReason.PROCEDURAL_SEQUENCE,
                DependencyReason.INCOMPLETE_SENTENCE,
            }
        )
        is_self_contained = not any_need and not dependency_marker_present
        if is_self_contained:
            _add_reason(reasons, DependencyReason.SELF_CONTAINED)

        confidence = _confidence(
            node,
            reasons,
            any_need=any_need,
            is_self_contained=is_self_contained,
            hierarchy_available=hierarchy is not None,
            parsed_reference_count=len(references),
        )

        return DependencySignal(
            source_chunk_id=node.chunk_id,
            needs_parent=needs_parent,
            needs_children=needs_children,
            needs_siblings=needs_siblings,
            needs_previous_neighbor=needs_previous_neighbor,
            needs_next_neighbor=needs_next_neighbor,
            needs_references=needs_references,
            is_self_contained=is_self_contained,
            confidence=confidence,
            reasons=reasons,
            matched_markers=matched_markers,
            metadata=metadata,
        )

    def detect_many(
        self,
        nodes: list[ProvisionNode],
        *,
        hierarchy: LegalProvisionHierarchyIndex | None = None,
        parsed_references_by_chunk: dict[str, list[LegalReference]] | None = None,
    ) -> list[DependencySignal]:
        references_by_chunk = parsed_references_by_chunk or {}
        return [
            self.detect(
                node,
                hierarchy=hierarchy,
                parsed_references=references_by_chunk.get(node.chunk_id),
            )
            for node in nodes
        ]

    def _point_needs_parent(self, node: ProvisionNode, parent_available: bool) -> bool:
        if node.parent_id:
            return True
        return _is_short_list_item(node) or parent_available

    def _point_needs_siblings(
        self,
        node: ProvisionNode,
        parent: ProvisionNode | None,
        hierarchy: LegalProvisionHierarchyIndex | None,
    ) -> bool:
        if hierarchy is None or parent is None:
            return False
        point_children = _point_children(hierarchy, parent)
        if len(point_children) <= 1:
            return False
        return bool(_find_markers(_parent_context(parent), LIST_INTRODUCTION_MARKERS))


def _point_children(hierarchy: LegalProvisionHierarchyIndex | None, parent: ProvisionNode) -> list[ProvisionNode]:
    if hierarchy is None:
        return []
    return [child for child in hierarchy.get_children(parent.chunk_id) if child.level == ProvisionLevel.POINT]


def _parent_context(parent: ProvisionNode | None) -> str:
    if parent is None:
        return ""
    return "\n".join(part for part in (parent.clause_lead_clean, parent.content_clean) if part)


def _is_short_list_item(node: ProvisionNode) -> bool:
    content = node.content_clean.strip()
    if not content:
        return False
    if POINT_MARKER_RE.match(content):
        return True
    if len(content) <= SHORT_LIST_ITEM_MAX_CHARS and node.level == ProvisionLevel.POINT:
        return not bool(SENTENCE_END_RE.search(content))
    return False


def _is_incomplete_content(content: str) -> bool:
    stripped = content.strip()
    return bool(stripped and stripped.endswith(":"))


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _find_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    normalized = _normalize_text(text)
    found: list[str] = []
    for marker in markers:
        if _normalize_text(marker) in normalized:
            found.append(marker)
    return found


def _normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _add_reason(reasons: list[DependencyReason], reason: DependencyReason) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _add_marker(markers: list[str], marker: str) -> None:
    if marker not in markers:
        markers.append(marker)


def _confidence(
    node: ProvisionNode,
    reasons: list[DependencyReason],
    *,
    any_need: bool,
    is_self_contained: bool,
    hierarchy_available: bool,
    parsed_reference_count: int,
) -> float:
    if is_self_contained:
        return SELF_CONTAINED_CONFIDENCE

    score = BASE_CONFIDENCE
    if any_need:
        score += 0.15
    if hierarchy_available:
        score += 0.08
    if node.level == ProvisionLevel.POINT and DependencyReason.POINT_HAS_CLAUSE_LEAD in reasons:
        score += 0.18
    if DependencyReason.PARENT_HAS_CHILDREN in reasons:
        score += 0.14
    if DependencyReason.LIST_INTRODUCTION in reasons:
        score += 0.1
    if DependencyReason.DIRECT_LEGAL_REFERENCE in reasons or DependencyReason.RELATIVE_LEGAL_REFERENCE in reasons:
        score += 0.12 if parsed_reference_count else 0.08
    if DependencyReason.EXCEPTION_MARKER in reasons:
        score += 0.08
    if DependencyReason.BACKWARD_DEPENDENCY in reasons or DependencyReason.FORWARD_DEPENDENCY in reasons:
        score += 0.08
    if DependencyReason.SHORT_LIST_ITEM in reasons and len(reasons) == 1:
        score -= 0.1
    return max(0.0, min(1.0, round(score, 3)))
