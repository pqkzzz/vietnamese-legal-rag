"""Text normalization helpers for legal document data."""

from __future__ import annotations

import re
import unicodedata


FOOTNOTE_RE = re.compile(r"\[\d+\]")
MULTI_SPACE_RE = re.compile(r"[ \t\f\v]+")
TOO_MANY_BLANK_LINES_RE = re.compile(r"\n{3,}")
REPEALED_RE = re.compile(r"(?:được|bị)\s+bãi\s+bỏ", re.IGNORECASE)
LEADING_MARKER_RE = re.compile(r"^\s*(?:\d+[.)]?|[a-zA-ZđĐ]\))\s*")


def compact_whitespace(value: str) -> str:
    """Collapse repeated spaces within each line and trim line edges."""

    lines = [MULTI_SPACE_RE.sub(" ", line).strip() for line in value.split("\n")]
    return TOO_MANY_BLANK_LINES_RE.sub("\n\n", "\n".join(lines)).strip()


def clean_legal_content(value: str) -> str:
    """Create safe searchable text while preserving legal wording."""

    normalized_newlines = value.replace("\r\n", "\n").replace("\r", "\n")
    without_footnotes = FOOTNOTE_RE.sub("", normalized_newlines)
    return compact_whitespace(without_footnotes)


def strip_consolidated_suffix(name: str) -> str:
    """Remove a final consolidated-document suffix when it is explicit."""

    return re.sub(r"\s*\(\s*Văn bản hợp nhất\b[^)]*\)\s*$", "", name).strip()


def normalize_for_matching(value: object) -> str:
    """Normalize text for case-insensitive Vietnamese comparisons."""

    text = str(value or "").strip().casefold()
    return MULTI_SPACE_RE.sub(" ", text)


def is_repealed_text(value: str) -> bool:
    """Return whether content says the provision was repealed."""

    return bool(REPEALED_RE.search(value))


def has_substantive_text(value: str) -> bool:
    """Return whether content has more than numbering or punctuation."""

    without_marker = LEADING_MARKER_RE.sub("", value).strip()
    for char in without_marker:
        category = unicodedata.category(char)
        if category.startswith("L") or category.startswith("N"):
            return True
    return False
