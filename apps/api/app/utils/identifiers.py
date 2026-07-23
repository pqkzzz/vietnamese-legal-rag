"""Identifier helpers for normalized legal units and retrieval chunks."""

from __future__ import annotations

import re


TARGET_ID_RE = re.compile(
    r"^(?P<law_id>.+?)_D(?P<article>[^_]+)(?:_K(?P<clause>[^_]+))?(?:_P(?P<point>[^_]+))?$"
)
POINT_SUFFIXES = {
    "a": "DA",
    "b": "DB",
    "c": "DC",
    "d": "DD",
    "đ": "DDD",
    "e": "DE",
    "g": "DG",
    "h": "DH",
    "i": "DI",
    "k": "DK",
    "l": "DL",
    "m": "DM",
    "n": "DN",
    "o": "DO",
    "p": "DP",
    "q": "DQ",
    "r": "DR",
    "s": "DS",
    "t": "DT",
    "u": "DU",
    "v": "DV",
    "x": "DX",
    "y": "DY",
}


def make_article_id(law_id: str, article_number: str) -> str:
    """Build the stable article identifier used by normalized units."""

    return f"{law_id}_D{article_number}"


def make_point_chunk_id(parent_clause_id: str, point_number: str) -> str:
    """Build a deterministic ASCII chunk ID for a point under a clause."""

    suffix = POINT_SUFFIXES.get(point_number.casefold())
    if suffix is None:
        raise ValueError(f"Unsupported legal point marker: {point_number}")
    return f"{parent_clause_id}_{suffix}"


def parse_target_unit_id(target_id: object) -> dict[str, str | None]:
    """Parse a known legal unit ID shape without inventing missing pieces."""

    empty = {
        "target_law_id": None,
        "target_article_number": None,
        "target_clause_number": None,
        "target_point_number": None,
    }
    if target_id is None:
        return empty

    match = TARGET_ID_RE.match(str(target_id).strip())
    if not match:
        return empty

    return {
        "target_law_id": match.group("law_id"),
        "target_article_number": match.group("article"),
        "target_clause_number": match.group("clause"),
        "target_point_number": match.group("point"),
    }
