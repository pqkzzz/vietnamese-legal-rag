"""Rule-based legal citation parser for Vietnamese legal queries."""

from __future__ import annotations

import re

from app.modules.query_understanding.models import LegalCitation
from app.modules.query_understanding.normalizer import fold_text, normalize_query

ARTICLE = r"(?P<article>\d+[a-zA-Z]?)"
CLAUSE = r"(?P<clause>\d+[a-zA-Z]?)"
POINT = r"(?P<point>a|b|c|d|dd|e|g|h|i|k|l|m|n|o|p|q|r|s|t|u|v|x|y)"

POINT_CLAUSE_ARTICLE_RE = re.compile(
    rf"\bdiem\s+{POINT}\s*,?\s*khoan\s+{CLAUSE}\s*,?\s*dieu\s+{ARTICLE}\b",
    re.IGNORECASE,
)
ARTICLE_CLAUSE_POINT_RE = re.compile(
    rf"\bdieu\s+{ARTICLE}\s*,?\s*khoan\s+{CLAUSE}(?:\s*,?\s*diem\s+{POINT})?\b",
    re.IGNORECASE,
)
CLAUSE_ARTICLE_RE = re.compile(
    rf"\bkhoan\s+{CLAUSE}\s*,?\s*dieu\s+{ARTICLE}\b",
    re.IGNORECASE,
)
MULTI_ARTICLE_RE = re.compile(
    r"\bcac\s+dieu\s+(?P<articles>\d+[a-zA-Z]?(?:\s*(?:,|va)\s*\d+[a-zA-Z]?)+)",
    re.IGNORECASE,
)
ARTICLE_RE = re.compile(r"\bdieu\s+(?P<article>\d+[a-zA-Z]?)\b", re.IGNORECASE)


class CitationParser:
    """Parse article, clause, and point citations from a query."""

    def parse(self, query: str) -> list[LegalCitation]:
        normalized = normalize_query(query)
        folded = fold_text(normalized)
        citations: list[LegalCitation] = []
        consumed: list[tuple[int, int]] = []

        for pattern in (POINT_CLAUSE_ARTICLE_RE, ARTICLE_CLAUSE_POINT_RE, CLAUSE_ARTICLE_RE):
            for match in pattern.finditer(folded):
                if _overlaps(match.span(), consumed):
                    continue
                citations.append(
                    LegalCitation(
                        article_number=match.group("article"),
                        clause_number=match.groupdict().get("clause"),
                        point_number=_normalize_point(match.groupdict().get("point")),
                        raw_text=normalized[match.start() : match.end()],
                        confidence=0.99,
                    )
                )
                consumed.append(match.span())

        for match in MULTI_ARTICLE_RE.finditer(folded):
            if _overlaps(match.span(), consumed):
                continue
            for article in re.findall(r"\d+[a-zA-Z]?", match.group("articles")):
                citations.append(
                    LegalCitation(
                        article_number=article,
                        raw_text=f"Dieu {article}",
                        confidence=0.95,
                    )
                )
            consumed.append(match.span())

        for match in ARTICLE_RE.finditer(folded):
            if _overlaps(match.span(), consumed):
                continue
            citations.append(
                LegalCitation(
                    article_number=match.group("article"),
                    raw_text=normalized[match.start() : match.end()],
                    confidence=0.95,
                )
            )
            consumed.append(match.span())

        return _dedupe(citations)


def _normalize_point(point: str | None) -> str | None:
    if point == "dd":
        return "đ"
    return point


def _overlaps(span: tuple[int, int], consumed: list[tuple[int, int]]) -> bool:
    return any(span[0] < end and span[1] > start for start, end in consumed)


def _dedupe(citations: list[LegalCitation]) -> list[LegalCitation]:
    seen: set[tuple[str | None, str | None, str | None]] = set()
    result: list[LegalCitation] = []
    for citation in citations:
        key = (citation.article_number, citation.clause_number, citation.point_number)
        if key not in seen:
            seen.add(key)
            result.append(citation)
    return result
