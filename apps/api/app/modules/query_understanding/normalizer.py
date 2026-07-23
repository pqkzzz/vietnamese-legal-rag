"""Normalize user legal queries without changing legal meaning."""

from __future__ import annotations

import re
import unicodedata

SPACE_RE = re.compile(r"\s+")
REPEATED_QUESTION_RE = re.compile(r"\?{2,}")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:?!])")


def normalize_query(query: str) -> str:
    """Return a clean NFC query while preserving numbers and citations."""

    normalized = unicodedata.normalize("NFC", query or "").strip()
    normalized = SPACE_RE.sub(" ", normalized)
    normalized = SPACE_BEFORE_PUNCT_RE.sub(r"\1", normalized)
    normalized = REPEATED_QUESTION_RE.sub("?", normalized)
    return normalized


def fold_text(value: str) -> str:
    """Casefold and remove Vietnamese accents for conservative matching."""

    lowered = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    return "".join(char for char in lowered if unicodedata.category(char) != "Mn")
