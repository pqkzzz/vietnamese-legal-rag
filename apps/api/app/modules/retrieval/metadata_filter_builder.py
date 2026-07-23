"""Build metadata filter plans from query understanding results."""

from __future__ import annotations

from typing import Any

from app.modules.query_understanding.law_resolver import HIGH_CONFIDENCE
from app.modules.query_understanding.models import MetadataFilterPlan, QueryUnderstandingResult

DEFAULT_FILTERS: dict[str, Any] = {
    "is_retrievable": True,
    "document_status": "effective",
    "provision_status": "effective",
}


class MetadataFilterBuilder:
    """Create conservative hard filters and routing hints for retrieval."""

    def build(self, understanding: QueryUnderstandingResult) -> MetadataFilterPlan:
        confident_laws = [
            law for law in understanding.resolved_laws if law.confidence >= HIGH_CONFIDENCE
        ]
        top_law = confident_laws[0] if len(confident_laws) == 1 else None
        top_citation = understanding.citations[0] if understanding.citations else None

        hard_filters: dict[str, Any] = dict(DEFAULT_FILTERS)
        reasons = ["default_effective_retrievable_filters"]

        if top_law is not None and not understanding.needs_clarification:
            hard_filters["law_id"] = top_law.law_id
            reasons.append("single_high_confidence_law")
        elif len(confident_laws) > 1:
            reasons.append("multiple_high_confidence_laws_no_law_filter")

        route = "broad_hybrid"
        if top_law is not None and top_citation is not None and top_citation.article_number:
            route = "exact_citation_lookup"
            _apply_citation_filters(hard_filters, top_citation.to_dict())
            reasons.append("high_confidence_law_with_citation")
        elif top_law is not None:
            route = "filtered_hybrid"
            reasons.append("high_confidence_law_without_citation")
        else:
            reasons.append("no_safe_law_filter")

        soft_hints: dict[str, Any] = {
            "intents": list(understanding.intents),
            "asks_current_law": understanding.asks_current_law,
        }
        if understanding.requested_year is not None:
            soft_hints["requested_year"] = understanding.requested_year
        if understanding.resolved_laws and top_law is None:
            soft_hints["law_candidates"] = [law.to_dict() for law in understanding.resolved_laws[:3]]
        if understanding.citations:
            soft_hints["citations"] = [citation.to_dict() for citation in understanding.citations]

        return MetadataFilterPlan(
            route=route,
            hard_filters=hard_filters,
            soft_hints=soft_hints,
            relaxation_steps=_build_relaxation_steps(hard_filters),
            reasons=reasons,
        )


def _apply_citation_filters(filters: dict[str, Any], citation: dict[str, Any]) -> None:
    for source, target in (
        ("article_number", "article_number"),
        ("clause_number", "clause_number"),
        ("point_number", "point_number"),
    ):
        value = citation.get(source)
        if value:
            filters[target] = str(value)


def _build_relaxation_steps(hard_filters: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    current = dict(hard_filters)
    steps.append(current)

    for field in ("point_number", "clause_number", "article_number", "law_id"):
        if field in current:
            current = dict(current)
            current.pop(field, None)
            if current not in steps:
                steps.append(current)

    return steps
