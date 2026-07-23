"""Identifier helpers for normalized legal units."""

from __future__ import annotations

import re


TARGET_ID_RE = re.compile(
    r"^(?P<law_id>.+?)_D(?P<article>[^_]+)(?:_K(?P<clause>[^_]+))?(?:_P(?P<point>[^_]+))?$"
)


def make_article_id(law_id: str, article_number: str) -> str:
    """Build the stable article identifier used by normalized units."""

    return f"{law_id}_D{article_number}"


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
