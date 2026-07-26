"""Data models for legal provision hierarchy indexing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ProvisionLevel(str, Enum):
    """Supported legal provision hierarchy levels."""

    ARTICLE = "article"
    CLAUSE = "clause"
    POINT = "point"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProvisionLocation:
    """A stable legal location key. Numeric identifiers stay strings."""

    law_id: str
    article_number: str | None
    clause_number: str | None = None
    point_number: str | None = None


@dataclass
class ProvisionNode:
    """One retrieval chunk represented as a legal hierarchy node."""

    qdrant_point_id: str | None
    chunk_id: str
    source_unit_id: str | None
    unit_type: str
    level: ProvisionLevel

    law_id: str
    law_name: str | None

    chapter_number: str | None
    chapter_title: str | None
    section_number: str | None
    section_title: str | None

    article_number: str | None
    article_title: str | None
    clause_number: str | None
    point_number: str | None

    article_id: str | None
    parent_id: str | None
    child_ids: tuple[str, ...]
    has_children: bool

    content_raw: str | None
    content_clean: str
    clause_lead_raw: str | None
    clause_lead_clean: str | None

    cross_references: list[dict[str, Any]]
    tags: list[str]

    provision_status: str | None
    is_retrievable: bool
    document_status: str | None

    order_index: int
    previous_sibling_id: str | None
    next_sibling_id: str | None

    metadata: dict[str, Any]

    @property
    def location(self) -> ProvisionLocation:
        return ProvisionLocation(
            law_id=self.law_id,
            article_number=self.article_number,
            clause_number=self.clause_number,
            point_number=self.point_number,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["level"] = self.level.value
        return payload


class LegalReferenceType(str, Enum):
    """Known legal reference source/target categories."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    RELATIVE = "relative"
    UNKNOWN = "unknown"


class ReferenceResolutionStatus(str, Enum):
    """Resolution outcome for one direct legal reference."""

    RESOLVED_EXACT = "resolved_exact"
    RESOLVED_MULTIPLE = "resolved_multiple"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


@dataclass(frozen=True)
class LegalReference:
    """A direct citation extracted from metadata or text."""

    source_chunk_id: str
    reference_type: LegalReferenceType

    target_law_id: str | None
    target_article_number: str | None
    target_clause_number: str | None
    target_point_number: str | None
    target_unit_id: str | None

    anchor_text: str | None
    description_summary: str | None
    raw_text: str | None

    confidence: float
    parser_source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reference_type"] = self.reference_type.value
        return payload


@dataclass(frozen=True)
class ResolvedLegalReference:
    """A parsed reference plus the target nodes it resolves to."""

    reference: LegalReference
    status: ReferenceResolutionStatus
    resolved_nodes: list[ProvisionNode]
    exact_node: ProvisionNode | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference.to_dict(),
            "status": self.status.value,
            "resolved_nodes": [node.to_dict() for node in self.resolved_nodes],
            "exact_node": self.exact_node.to_dict() if self.exact_node else None,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ReferenceResolutionBatch:
    """Direct references parsed and resolved for one source node."""

    source_chunk_id: str
    references: list[LegalReference]
    resolved_references: list[ResolvedLegalReference]
    resolved_count: int
    unresolved_count: int
    ambiguous_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_chunk_id": self.source_chunk_id,
            "references": [reference.to_dict() for reference in self.references],
            "resolved_references": [reference.to_dict() for reference in self.resolved_references],
            "resolved_count": self.resolved_count,
            "unresolved_count": self.unresolved_count,
            "ambiguous_count": self.ambiguous_count,
            "warnings": list(self.warnings),
        }


class DependencyReason(str, Enum):
    """Stable rule identifiers emitted by the legal dependency detector."""

    POINT_REQUIRES_PARENT = "POINT_REQUIRES_PARENT"
    POINT_HAS_CLAUSE_LEAD = "POINT_HAS_CLAUSE_LEAD"
    SHORT_LIST_ITEM = "SHORT_LIST_ITEM"
    PARENT_HAS_CHILDREN = "PARENT_HAS_CHILDREN"
    LIST_INTRODUCTION = "LIST_INTRODUCTION"
    DIRECT_LEGAL_REFERENCE = "DIRECT_LEGAL_REFERENCE"
    RELATIVE_LEGAL_REFERENCE = "RELATIVE_LEGAL_REFERENCE"
    EXCEPTION_MARKER = "EXCEPTION_MARKER"
    FORWARD_DEPENDENCY = "FORWARD_DEPENDENCY"
    BACKWARD_DEPENDENCY = "BACKWARD_DEPENDENCY"
    PROCEDURAL_SEQUENCE = "PROCEDURAL_SEQUENCE"
    INCOMPLETE_SENTENCE = "INCOMPLETE_SENTENCE"
    SELF_CONTAINED = "SELF_CONTAINED"


@dataclass(frozen=True)
class DependencySignal:
    """Query-independent context needs detected for one provision node."""

    source_chunk_id: str

    needs_parent: bool
    needs_children: bool
    needs_siblings: bool
    needs_previous_neighbor: bool
    needs_next_neighbor: bool
    needs_references: bool

    is_self_contained: bool
    confidence: float

    reasons: list[DependencyReason]
    matched_markers: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = [reason.value for reason in self.reasons]
        return payload

@dataclass(frozen=True)
class HierarchyWarning:
    """A structured warning emitted while building a hierarchy index."""

    code: str
    message: str
    chunk_id: str | None = None
    related_chunk_id: str | None = None
    source_file: str | None = None
    line_number: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HierarchyBuildReport:
    """Summary of a hierarchy index build."""

    source_files: list[str]
    total_records: int
    total_nodes: int
    article_nodes: int
    clause_nodes: int
    point_nodes: int
    retrievable_nodes: int
    non_retrievable_nodes: int
    orphan_nodes: int
    duplicate_chunk_ids: int
    duplicate_locations: int
    warning_count: int
    warnings: list[HierarchyWarning]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = [warning.to_dict() for warning in self.warnings]
        return payload


@dataclass(frozen=True)
class ProvisionLookupResult:
    """Structured result for article, clause, or point hierarchy lookup."""

    location: ProvisionLocation
    exact_node: ProvisionNode | None
    nodes: list[ProvisionNode]
    matched_level: ProvisionLevel | None
    found: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "location": asdict(self.location),
            "exact_node": self.exact_node.to_dict() if self.exact_node else None,
            "nodes": [node.to_dict() for node in self.nodes],
            "matched_level": self.matched_level.value if self.matched_level else None,
            "found": self.found,
            "warnings": list(self.warnings),
        }

