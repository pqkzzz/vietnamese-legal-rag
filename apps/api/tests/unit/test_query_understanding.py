from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

API_ROOT = Path(__file__).resolve().parents[2]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.modules.query_understanding import QueryUnderstandingService
from app.modules.query_understanding.citation_parser import CitationParser
from app.modules.query_understanding.intent_classifier import IntentClassifier
from app.modules.query_understanding.law_resolver import LawResolver
from app.modules.query_understanding.normalizer import normalize_query
from app.modules.retrieval.metadata_filter_builder import MetadataFilterBuilder
from app.modules.retrieval.query_aware_retriever import QueryAwareRetriever
import app.modules.retrieval.query_aware_retriever as query_aware_module


@dataclass(frozen=True)
class FakeHybridResult:
    point_id: str
    score: float
    payload: dict[str, object]


class FakeHybridRetriever:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def search(self, query: str, *, limit: int = 10, law_id: str | None = None) -> list[FakeHybridResult]:
        self.calls.append({"query": query, "limit": limit, "law_id": law_id})
        return [FakeHybridResult("p1", 1.0, {"law_id": law_id})]


class FakeQdrantModels:
    class MatchValue:
        def __init__(self, value: object) -> None:
            self.value = value

    class FieldCondition:
        def __init__(self, key: str, match: object) -> None:
            self.key = key
            self.match = match

    class Filter:
        def __init__(self, must: list[object]) -> None:
            self.must = must


class FakeQdrantClient:
    def __init__(self) -> None:
        self.filters: list[object] = []

    def scroll(self, **kwargs: object) -> tuple[list[object], None]:
        self.filters.append(kwargs["scroll_filter"])
        point = SimpleNamespace(
            id="point-121",
            score=None,
            payload={"law_id": "LDD_2024", "article_number": "121"},
        )
        return [point], None


def test_normalizer_keeps_legal_numbers_and_trims_spacing() -> None:
    assert normalize_query("  Điều   121   ? ? ") == "Điều 121?"


def test_citation_parser_extracts_point_clause_article() -> None:
    citations = CitationParser().parse("Theo điểm b khoản 1 Điều 121 Luật Đất đai 2024")
    assert citations[0].article_number == "121"
    assert citations[0].clause_number == "1"
    assert citations[0].point_number == "b"


def test_law_resolver_requires_explicit_law_mention_for_generic_alias() -> None:
    resolver = LawResolver()
    generic_results, _, _ = resolver.resolve(
        "Chủ đầu tư có phải được ngân hàng bảo lãnh trước khi bán nhà ở hình thành trong tương lai không?"
    )
    assert generic_results == []

    explicit_results, _, _ = resolver.resolve("Theo Luật Nhà ở 2023, người nước ngoài có được sở hữu nhà ở không?")
    assert explicit_results[0].law_id == "LNO_2023"
    assert explicit_results[0].confidence >= 0.9


def test_intent_classifier_is_multi_label() -> None:
    intents = IntentClassifier().classify("Điều kiện và thủ tục cấp giấy chứng nhận mất bao lâu?")
    assert "condition" in intents
    assert "procedure" in intents
    assert "deadline" in intents


def test_filter_builder_routes_exact_citation() -> None:
    understanding = QueryUnderstandingService().understand(
        "Theo điểm b khoản 1 Điều 121 Luật Đất đai 2024, trường hợp nào được cấp giấy chứng nhận?"
    )
    plan = MetadataFilterBuilder().build(understanding)
    assert plan.route == "exact_citation_lookup"
    assert plan.hard_filters["law_id"] == "LDD_2024"
    assert plan.hard_filters["article_number"] == "121"
    assert plan.hard_filters["clause_number"] == "1"
    assert plan.hard_filters["point_number"] == "b"
    assert plan.relaxation_steps[-1]["is_retrievable"] is True
    assert "law_id" not in plan.relaxation_steps[-1]


def test_filter_builder_routes_broad_when_no_safe_law() -> None:
    understanding = QueryUnderstandingService().understand(
        "Chủ đầu tư có phải được ngân hàng bảo lãnh trước khi bán nhà ở hình thành trong tương lai không?"
    )
    plan = MetadataFilterBuilder().build(understanding)
    assert plan.route == "broad_hybrid"
    assert "law_id" not in plan.hard_filters


def test_query_aware_retriever_uses_filtered_hybrid() -> None:
    hybrid = FakeHybridRetriever()
    retriever = QueryAwareRetriever(hybrid_retriever=hybrid)  # type: ignore[arg-type]
    response = retriever.search("Theo Luật Nhà ở 2023, người nước ngoài có được sở hữu nhà ở không?", limit=3)
    assert response.route_used == "filtered_hybrid"
    assert hybrid.calls[0]["law_id"] == "LNO_2023"


def test_query_aware_retriever_uses_exact_qdrant_lookup(monkeypatch) -> None:
    monkeypatch.setattr(query_aware_module, "models", FakeQdrantModels)
    client = FakeQdrantClient()
    hybrid = FakeHybridRetriever()
    retriever = QueryAwareRetriever(
        hybrid_retriever=hybrid,  # type: ignore[arg-type]
        qdrant_client=client,
        collection_name="legal_units_bge_m3_finetuned",
    )
    response = retriever.search(
        "Theo điểm b khoản 1 Điều 121 Luật Đất đai 2024, trường hợp nào được cấp giấy chứng nhận?",
        limit=3,
    )
    assert response.route_used == "exact_citation_lookup"
    assert response.results[0]["payload"]["law_id"] == "LDD_2024"
    assert hybrid.calls == []

