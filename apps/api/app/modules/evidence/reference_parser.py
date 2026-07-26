"""Parse direct legal references from evidence hierarchy nodes."""

from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from typing import Any

from app.modules.evidence.models import LegalReference, LegalReferenceType, ProvisionNode
from app.utils.identifiers import parse_target_unit_id

PARSER_SOURCE_STRUCTURED = "structured_metadata"
PARSER_SOURCE_RAW_REFERENCE = "raw_reference"
PARSER_SOURCE_CONTENT_REGEX = "content_regex"

STRUCTURED_CONFIDENCE = 0.95
STRUCTURED_CONFLICT_CONFIDENCE = 0.75
REGEX_POINT_CONFIDENCE = 0.86
REGEX_CLAUSE_CONFIDENCE = 0.82
REGEX_ARTICLE_CONFIDENCE = 0.72
REGEX_RELATIVE_CONFIDENCE = 0.84

ARTICLE = r"(?P<article>\d+[a-zA-Z]?)"
CLAUSE = r"(?P<clause>\d+[a-zA-Z]?)"
POINT = r"(?P<point>a|b|c|d|e|g|h|i|k|l|m|n|o|p|q|r|s|t|u|v|x|y)"

POINT_CLAUSE_ARTICLE_RE = re.compile(
    rf"\bdiem\s+{POINT}\s+khoan\s+{CLAUSE}\s+dieu\s+{ARTICLE}\b",
    re.IGNORECASE,
)
CLAUSE_ARTICLE_RE = re.compile(
    rf"\bkhoan\s+{CLAUSE}\s+dieu\s+{ARTICLE}\b",
    re.IGNORECASE,
)
RELATIVE_CLAUSE_RE = re.compile(r"\bkhoan\s+(?P<clause>\d+[a-zA-Z]?)\s+dieu\s+nay\b", re.IGNORECASE)
RELATIVE_ARTICLE_RE = re.compile(r"\bdieu\s+nay\b", re.IGNORECASE)
MULTI_ARTICLE_RE = re.compile(
    r"\bcac\s+dieu\s+(?P<articles>\d+[a-zA-Z]?(?:\s*(?:,|va)\s*\d+[a-zA-Z]?)+)",
    re.IGNORECASE,
)
ARTICLE_RE = re.compile(r"\bdieu\s+(?P<article>\d+[a-zA-Z]?)\b", re.IGNORECASE)


class LegalReferenceParser:
    """Parse direct legal references from structured metadata and text.

    Structured cross-reference metadata is kept first and wins deduplication.
    Regex parsing is conservative and only matches explicit legal markers such
    as dieu, khoan, and diem.
    """

    def parse_node(self, node: ProvisionNode) -> list[LegalReference]:
        references: list[LegalReference] = []
        seen: set[tuple[str | None, str | None, str | None, str | None, str | None]] = set()

        for value in node.cross_references:
            reference = self.parse_structured_reference(node, value)
            if reference is not None:
                self._add_unique(references, seen, reference)
                for fallback in self._parse_raw_reference(node, value):
                    self._add_unique(references, seen, fallback)

        for reference in self.parse_text(node, node.content_clean):
            self._add_unique(references, seen, reference)

        return references

    def parse_structured_reference(self, source_node: ProvisionNode, value: dict[str, Any]) -> LegalReference | None:
        if not isinstance(value, dict):
            return None

        reference_type = _reference_type(value.get("reference_type"))
        target_unit_id = _string_or_none(value.get("target_unit_id"))
        parsed_id = parse_target_unit_id(target_unit_id)
        target_law_id = _first_string(value.get("target_law_id"), parsed_id["target_law_id"])
        if target_law_id is None and reference_type == LegalReferenceType.INTERNAL:
            target_law_id = source_node.law_id

        target_article_number = _first_string(value.get("target_article_number"), parsed_id["target_article_number"])
        target_clause_number = _first_string(value.get("target_clause_number"), parsed_id["target_clause_number"])
        target_point_number = _first_string(value.get("target_point_number"), parsed_id["target_point_number"])
        metadata = deepcopy(value)
        warnings = _location_conflict_warnings(
            target_unit_id,
            target_law_id,
            target_article_number,
            target_clause_number,
            target_point_number,
        )
        confidence = STRUCTURED_CONFLICT_CONFIDENCE if warnings else STRUCTURED_CONFIDENCE
        if warnings:
            metadata["warnings"] = warnings

        raw_reference = value.get("raw_reference")
        raw_text = raw_reference if isinstance(raw_reference, str) else _string_or_none(value.get("anchor_text"))
        return LegalReference(
            source_chunk_id=source_node.chunk_id,
            reference_type=reference_type,
            target_law_id=target_law_id,
            target_article_number=target_article_number,
            target_clause_number=target_clause_number,
            target_point_number=target_point_number,
            target_unit_id=target_unit_id,
            anchor_text=_string_or_none(value.get("anchor_text")),
            description_summary=_string_or_none(value.get("description_summary")),
            raw_text=raw_text,
            confidence=confidence,
            parser_source=PARSER_SOURCE_STRUCTURED,
            metadata=metadata,
        )

    def parse_text(self, source_node: ProvisionNode, text: str) -> list[LegalReference]:
        normalized = _collapse_spaces(text)
        folded = _fold_text(normalized)
        references: list[LegalReference] = []
        consumed: list[tuple[int, int]] = []

        for pattern, level in (
            (POINT_CLAUSE_ARTICLE_RE, "point"),
            (RELATIVE_CLAUSE_RE, "relative_clause"),
            (CLAUSE_ARTICLE_RE, "clause"),
        ):
            for match in pattern.finditer(folded):
                if _overlaps(match.span(), consumed):
                    continue
                references.append(self._reference_from_match(source_node, normalized, match, level))
                consumed.append(match.span())

        for match in MULTI_ARTICLE_RE.finditer(folded):
            if _overlaps(match.span(), consumed):
                continue
            for article_number in re.findall(r"\d+[a-zA-Z]?", match.group("articles")):
                references.append(
                    _text_reference(
                        source_node,
                        target_article_number=article_number,
                        raw_text=f"Điều {article_number}",
                        confidence=REGEX_ARTICLE_CONFIDENCE,
                    )
                )
            consumed.append(match.span())

        for match in RELATIVE_ARTICLE_RE.finditer(folded):
            if _overlaps(match.span(), consumed):
                continue
            if source_node.article_number:
                references.append(
                    _text_reference(
                        source_node,
                        reference_type=LegalReferenceType.RELATIVE,
                        target_article_number=source_node.article_number,
                        raw_text=_raw_slice(normalized, match.span()),
                        confidence=REGEX_RELATIVE_CONFIDENCE,
                    )
                )
            consumed.append(match.span())

        for match in ARTICLE_RE.finditer(folded):
            if _overlaps(match.span(), consumed):
                continue
            references.append(
                _text_reference(
                    source_node,
                    target_article_number=match.group("article"),
                    raw_text=_raw_slice(normalized, match.span()),
                    confidence=REGEX_ARTICLE_CONFIDENCE,
                )
            )
            consumed.append(match.span())

        return _dedupe(references)

    def _reference_from_match(self, source_node: ProvisionNode, original: str, match: re.Match[str], level: str) -> LegalReference:
        raw_text = _raw_slice(original, match.span())
        if level == "point":
            return _text_reference(
                source_node,
                target_article_number=match.group("article"),
                target_clause_number=match.group("clause"),
                target_point_number=_point_from_raw(raw_text, match.group("point")),
                raw_text=raw_text,
                confidence=REGEX_POINT_CONFIDENCE,
            )
        if level == "relative_clause":
            return _text_reference(
                source_node,
                reference_type=LegalReferenceType.RELATIVE,
                target_article_number=source_node.article_number,
                target_clause_number=match.group("clause"),
                raw_text=raw_text,
                confidence=REGEX_RELATIVE_CONFIDENCE,
            )
        return _text_reference(
            source_node,
            target_article_number=match.group("article"),
            target_clause_number=match.group("clause"),
            raw_text=raw_text,
            confidence=REGEX_CLAUSE_CONFIDENCE,
        )

    def _parse_raw_reference(self, source_node: ProvisionNode, value: dict[str, Any]) -> list[LegalReference]:
        raw_reference = value.get("raw_reference")
        texts: list[str] = []
        if isinstance(raw_reference, str):
            texts.append(raw_reference)
        elif isinstance(raw_reference, dict):
            for key in ("anchor_text", "description_summary"):
                text = _string_or_none(raw_reference.get(key))
                if text:
                    texts.append(text)
        anchor_text = _string_or_none(value.get("anchor_text"))
        if anchor_text:
            texts.append(anchor_text)

        references: list[LegalReference] = []
        for text in texts:
            for reference in self.parse_text(source_node, text):
                references.append(
                    LegalReference(
                        source_chunk_id=reference.source_chunk_id,
                        reference_type=reference.reference_type,
                        target_law_id=reference.target_law_id,
                        target_article_number=reference.target_article_number,
                        target_clause_number=reference.target_clause_number,
                        target_point_number=reference.target_point_number,
                        target_unit_id=reference.target_unit_id,
                        anchor_text=reference.anchor_text,
                        description_summary=reference.description_summary,
                        raw_text=reference.raw_text,
                        confidence=min(reference.confidence, REGEX_CLAUSE_CONFIDENCE),
                        parser_source=PARSER_SOURCE_RAW_REFERENCE,
                        metadata={"raw_reference": deepcopy(value)},
                    )
                )
        return references

    def _add_unique(
        self,
        references: list[LegalReference],
        seen: set[tuple[str | None, str | None, str | None, str | None, str | None]],
        reference: LegalReference,
    ) -> None:
        key = _canonical_key(reference)
        if key not in seen:
            seen.add(key)
            references.append(reference)


def _text_reference(
    source_node: ProvisionNode,
    *,
    target_article_number: str | None,
    target_clause_number: str | None = None,
    target_point_number: str | None = None,
    reference_type: LegalReferenceType = LegalReferenceType.INTERNAL,
    raw_text: str | None,
    confidence: float,
) -> LegalReference:
    return LegalReference(
        source_chunk_id=source_node.chunk_id,
        reference_type=reference_type,
        target_law_id=source_node.law_id,
        target_article_number=target_article_number,
        target_clause_number=target_clause_number,
        target_point_number=target_point_number,
        target_unit_id=None,
        anchor_text=raw_text,
        description_summary=None,
        raw_text=raw_text,
        confidence=confidence,
        parser_source=PARSER_SOURCE_CONTENT_REGEX,
        metadata={},
    )


def _dedupe(references: list[LegalReference]) -> list[LegalReference]:
    result: list[LegalReference] = []
    seen: set[tuple[str | None, str | None, str | None, str | None, str | None]] = set()
    for reference in references:
        key = _canonical_key(reference)
        if key not in seen:
            seen.add(key)
            result.append(reference)
    return result


def _canonical_key(reference: LegalReference) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    parsed_id = parse_target_unit_id(reference.target_unit_id)
    law_id = reference.target_law_id or parsed_id["target_law_id"]
    article = reference.target_article_number or parsed_id["target_article_number"]
    clause = reference.target_clause_number or parsed_id["target_clause_number"]
    point = reference.target_point_number or parsed_id["target_point_number"]
    if law_id or article:
        return (law_id, article, clause, point, None)
    return (None, None, None, None, reference.target_unit_id)


def _location_conflict_warnings(
    target_unit_id: str | None,
    law_id: str | None,
    article: str | None,
    clause: str | None,
    point: str | None,
) -> list[str]:
    if not target_unit_id:
        return []
    parsed = parse_target_unit_id(target_unit_id)
    warnings: list[str] = []
    for name, explicit, parsed_value in (
        ("target_law_id", law_id, parsed["target_law_id"]),
        ("target_article_number", article, parsed["target_article_number"]),
        ("target_clause_number", clause, parsed["target_clause_number"]),
        ("target_point_number", point, parsed["target_point_number"]),
    ):
        if explicit and parsed_value and explicit != parsed_value:
            warnings.append(f"{name} conflicts with target_unit_id")
    return warnings


def _reference_type(value: object) -> LegalReferenceType:
    text = _string_or_none(value)
    if text in {item.value for item in LegalReferenceType}:
        return LegalReferenceType(text)
    return LegalReferenceType.UNKNOWN


def _first_string(*values: object) -> str | None:
    for value in values:
        text = _string_or_none(value)
        if text is not None:
            return text
    return None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _fold_text(value: str) -> str:
    lowered = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(char for char in lowered if unicodedata.category(char) != "Mn")


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _overlaps(span: tuple[int, int], consumed: list[tuple[int, int]]) -> bool:
    return any(span[0] < end and span[1] > start for start, end in consumed)


def _raw_slice(original: str, span: tuple[int, int]) -> str:
    return original[span[0] : span[1]].strip()


def _point_from_raw(raw_text: str, folded_point: str) -> str:
    match = re.search(r"điểm\s+(?P<point>[a-zA-ZđĐ])", raw_text, re.IGNORECASE)
    if match:
        point = match.group("point").casefold()
        if point == "đ":
            return "đ"
        return point
    return folded_point
