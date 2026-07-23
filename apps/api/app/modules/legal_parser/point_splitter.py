"""Split Vietnamese legal clauses into point-level child units."""

from __future__ import annotations

from dataclasses import dataclass
import re


LEGAL_POINT_ORDER = [
    "a", "b", "c", "d", "đ", "e",
    "g", "h", "i", "k", "l", "m",
    "n", "o", "p", "q", "r", "s",
    "t", "u", "v", "x", "y",
]
LEGAL_POINT_INDEX = {marker: index for index, marker in enumerate(LEGAL_POINT_ORDER)}
POINT_MARKER_PATTERN = re.compile(
    r"^[ \t]*(?P<marker>a|b|c|d|đ|e|g|h|i|k|l|m|n|o|p|q|r|s|t|u|v|x|y)\)\s*(?:\[\d+\]\s*)?",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class SplitPoint:
    """One point split from a parent legal clause."""

    point_number: str
    marker: str
    content_raw: str
    content_clean: str


@dataclass(frozen=True)
class PointSplitResult:
    """Result of attempting to split a clause into legal points."""

    was_split: bool
    clause_lead_raw: str
    clause_lead_clean: str
    points: list[SplitPoint]
    warnings: list[dict[str, str | None]]


def split_clause_points(content_raw: str, content_clean: str) -> PointSplitResult:
    """Split a clause into point children when markers are reliable.

    Markers are recognized only at line starts, after optional indentation. Raw
    consolidated text may place footnotes like ``b)[45]`` immediately after the
    marker; those still represent the same point marker as clean text ``b)``.
    """

    raw_matches = list(POINT_MARKER_PATTERN.finditer(content_raw))
    clean_matches = list(POINT_MARKER_PATTERN.finditer(content_clean))
    raw_markers = [_normalize_marker(match.group("marker")) for match in raw_matches]
    clean_markers = [_normalize_marker(match.group("marker")) for match in clean_matches]

    if len(clean_matches) < 2:
        return PointSplitResult(False, content_raw, content_clean, [], [])
    if raw_markers != clean_markers:
        return _unsplit(content_raw, content_clean, "POINT_MARKER_MISMATCH", "Raw and clean point markers do not match.")

    sequence_warning = _sequence_warning(clean_markers)
    if sequence_warning is not None:
        return _unsplit(content_raw, content_clean, sequence_warning["code"], sequence_warning["message"])

    raw_segments = _slice_segments(content_raw, raw_matches)
    clean_segments = _slice_segments(content_clean, clean_matches)
    if any(not _has_point_body(segment, marker) for segment, marker in zip(clean_segments, clean_markers)):
        return _unsplit(content_raw, content_clean, "EMPTY_POINT_CONTENT", "At least one point marker has no content.")

    points = [
        SplitPoint(point_number=marker, marker=f"{marker})", content_raw=raw_segment.strip(), content_clean=clean_segment.strip())
        for marker, raw_segment, clean_segment in zip(clean_markers, raw_segments, clean_segments)
    ]
    return PointSplitResult(
        was_split=True,
        clause_lead_raw=content_raw[: raw_matches[0].start()].strip(),
        clause_lead_clean=content_clean[: clean_matches[0].start()].strip(),
        points=points,
        warnings=[],
    )


def strip_leading_clause_number(value: str) -> str:
    """Remove only a leading clause number used in embedding context."""

    return re.sub(r"^\s*\d+[.)]?\s*", "", value, count=1).strip()


def strip_leading_point_marker(value: str) -> str:
    """Remove only a leading legal point marker used in embedding context."""

    return POINT_MARKER_PATTERN.sub("", value, count=1).strip()


def _slice_segments(content: str, matches: list[re.Match[str]]) -> list[str]:
    segments: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        segments.append(content[match.start() : end])
    return segments


def _sequence_warning(markers: list[str]) -> dict[str, str] | None:
    if not markers or markers[0] != "a":
        return {"code": "INVALID_POINT_SEQUENCE", "message": "Point marker sequence must start with a)."}
    indexes = [LEGAL_POINT_INDEX[marker] for marker in markers]
    if indexes != sorted(indexes) or len(set(indexes)) != len(indexes):
        return {"code": "INVALID_POINT_SEQUENCE", "message": "Point marker sequence is not in valid legal order."}
    return None


def _has_point_body(segment: str, marker: str) -> bool:
    body = re.sub(
        rf"^[ \t]*{re.escape(marker)}\)\s*(?:\[\d+\]\s*)?",
        "",
        segment,
        count=1,
        flags=re.IGNORECASE | re.MULTILINE,
    ).strip()
    return bool(body)


def _normalize_marker(marker: str) -> str:
    return marker.casefold()


def _unsplit(content_raw: str, content_clean: str, code: str, message: str) -> PointSplitResult:
    return PointSplitResult(
        was_split=False,
        clause_lead_raw=content_raw,
        clause_lead_clean=content_clean,
        points=[],
        warnings=[{"unit_id": None, "field": "content_clean", "code": code, "message": message}],
    )
