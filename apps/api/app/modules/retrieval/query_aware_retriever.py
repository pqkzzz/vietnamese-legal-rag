"""Query-aware retrieval orchestration."""

from __future__ import annotations

import time
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

from app.modules.query_understanding import QueryUnderstandingService
from app.modules.query_understanding.models import QueryAwareSearchResponse
from app.modules.retrieval.metadata_filter_builder import MetadataFilterBuilder

if TYPE_CHECKING:
    from app.modules.retrieval.hybrid_retriever import HybridLegalRetriever

try:  # pragma: no cover - exercised only when qdrant-client is installed.
    from qdrant_client.http import models
except Exception:  # pragma: no cover
    models = None  # type: ignore[assignment]


class QueryAwareRetriever:
    """Route legal queries using local query understanding metadata."""

    def __init__(
        self,
        *,
        hybrid_retriever: "HybridLegalRetriever",
        understanding_service: QueryUnderstandingService | None = None,
        filter_builder: MetadataFilterBuilder | None = None,
        qdrant_client: Any | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.hybrid_retriever = hybrid_retriever
        self.understanding_service = understanding_service or QueryUnderstandingService()
        self.filter_builder = filter_builder or MetadataFilterBuilder()
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name

    def search(self, query: str, *, limit: int = 10) -> QueryAwareSearchResponse:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        start = time.perf_counter()
        understanding = self.understanding_service.understand(query)
        plan = self.filter_builder.build(understanding)
        warnings = list(understanding.warnings)
        route_used = plan.route
        relaxation_level = 0

        if plan.route == "exact_citation_lookup":
            results, relaxation_level = self._exact_lookup(plan.relaxation_steps, limit)
            if results:
                latency = round(time.perf_counter() - start, 4)
                return QueryAwareSearchResponse(
                    query_understanding=understanding,
                    filter_plan=plan,
                    route_used=route_used,
                    relaxation_level=relaxation_level,
                    results=results,
                    warnings=warnings,
                    latency=latency,
                )
            warnings.append("Exact citation lookup returned no results; fell back to filtered hybrid.")
            route_used = "filtered_hybrid"

        law_id = plan.hard_filters.get("law_id") if route_used == "filtered_hybrid" else None
        hybrid_results = self.hybrid_retriever.search(query, limit=limit, law_id=law_id)
        latency = round(time.perf_counter() - start, 4)
        return QueryAwareSearchResponse(
            query_understanding=understanding,
            filter_plan=plan,
            route_used=route_used,
            relaxation_level=relaxation_level,
            results=[_serialize_result(result) for result in hybrid_results],
            warnings=warnings,
            latency=latency,
        )

    def _exact_lookup(self, relaxation_steps: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], int]:
        if self.qdrant_client is None or not self.collection_name:
            return [], 0
        if models is None:
            return [], 0

        for index, filters in enumerate(relaxation_steps):
            scroll_filter = _to_qdrant_filter(filters)
            response = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            points = response[0] if isinstance(response, tuple) else response
            results = [_serialize_point(point) for point in points]
            if results:
                return results, index
        return [], max(len(relaxation_steps) - 1, 0)


def _to_qdrant_filter(filters: dict[str, Any]) -> Any:
    if models is None:  # pragma: no cover
        return None
    return models.Filter(
        must=[
            models.FieldCondition(key=key, match=models.MatchValue(value=value))
            for key, value in filters.items()
        ]
    )


def _serialize_point(point: Any) -> dict[str, Any]:
    return {
        "point_id": str(getattr(point, "id", "")),
        "score": getattr(point, "score", None),
        "payload": dict(getattr(point, "payload", {}) or {}),
    }


def _serialize_result(result: Any) -> Any:
    if is_dataclass(result):
        return asdict(result)
    if hasattr(result, "to_dict"):
        return result.to_dict()
    return result


