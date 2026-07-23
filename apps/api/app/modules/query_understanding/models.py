"""Data models for rule-based query understanding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LegalCitation:
    article_number: str | None = None
    clause_number: str | None = None
    point_number: str | None = None
    raw_text: str | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedLaw:
    law_id: str
    official_title: str
    matched_text: str
    match_type: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryUnderstandingResult:
    raw_query: str
    normalized_query: str
    resolved_laws: list[ResolvedLaw] = field(default_factory=list)
    citations: list[LegalCitation] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    requested_year: int | None = None
    asks_current_law: bool = False
    overall_confidence: float = 0.0
    needs_clarification: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resolved_laws"] = [law.to_dict() for law in self.resolved_laws]
        payload["citations"] = [citation.to_dict() for citation in self.citations]
        return payload


@dataclass(frozen=True)
class MetadataFilterPlan:
    route: str
    hard_filters: dict[str, Any] = field(default_factory=dict)
    soft_hints: dict[str, Any] = field(default_factory=dict)
    relaxation_steps: list[dict[str, Any]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryAwareSearchResponse:
    query_understanding: QueryUnderstandingResult
    filter_plan: MetadataFilterPlan
    route_used: str
    relaxation_level: int
    results: list[Any]
    warnings: list[str]
    latency: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_understanding": self.query_understanding.to_dict(),
            "filter_plan": self.filter_plan.to_dict(),
            "route_used": self.route_used,
            "relaxation_level": self.relaxation_level,
            "results": self.results,
            "warnings": self.warnings,
            "latency": self.latency,
        }
