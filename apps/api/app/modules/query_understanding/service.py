"""High-level query understanding service."""

from __future__ import annotations

import re

from app.modules.query_understanding.citation_parser import CitationParser
from app.modules.query_understanding.intent_classifier import IntentClassifier
from app.modules.query_understanding.law_resolver import LawResolver
from app.modules.query_understanding.models import QueryUnderstandingResult
from app.modules.query_understanding.normalizer import fold_text, normalize_query

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
CURRENT_MARKERS = ("hien hanh", "hien nay", "luat hien hanh", "theo quy dinh hien hanh")
COMPLEX_TIME_MARKERS = ("truoc ngay", "sau ngay", "luat cu")


class QueryUnderstandingService:
    """Run local rule-based query understanding."""

    def __init__(
        self,
        law_resolver: LawResolver | None = None,
        citation_parser: CitationParser | None = None,
        intent_classifier: IntentClassifier | None = None,
    ) -> None:
        self.law_resolver = law_resolver or LawResolver()
        self.citation_parser = citation_parser or CitationParser()
        self.intent_classifier = intent_classifier or IntentClassifier()

    def understand(self, query: str) -> QueryUnderstandingResult:
        normalized = normalize_query(query)
        resolved_laws, law_warnings, needs_clarification = self.law_resolver.resolve(normalized)
        citations = self.citation_parser.parse(normalized)
        intents = self.intent_classifier.classify(normalized)
        requested_year = _requested_year(normalized)
        folded = fold_text(normalized)
        asks_current_law = any(marker in folded for marker in CURRENT_MARKERS)
        warnings = list(law_warnings)
        if any(marker in folded for marker in COMPLEX_TIME_MARKERS):
            warnings.append("Complex temporal expression detected; legal effect is not inferred in this version.")
        confidence_parts: list[float] = []
        if resolved_laws:
            confidence_parts.append(resolved_laws[0].confidence)
        if citations:
            confidence_parts.append(max(citation.confidence for citation in citations))
        overall = round(sum(confidence_parts) / len(confidence_parts), 3) if confidence_parts else 0.0
        return QueryUnderstandingResult(
            raw_query=query,
            normalized_query=normalized,
            resolved_laws=resolved_laws,
            citations=citations,
            intents=intents,
            requested_year=requested_year,
            asks_current_law=asks_current_law,
            overall_confidence=overall,
            needs_clarification=needs_clarification,
            warnings=warnings,
        )


def _requested_year(query: str) -> int | None:
    matches = YEAR_RE.findall(query)
    return int(matches[-1]) if matches else None
