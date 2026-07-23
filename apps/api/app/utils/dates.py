"""Date parsing helpers for legal document normalization."""

from __future__ import annotations

from datetime import datetime


SUPPORTED_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def parse_date_to_iso(value: object) -> str | None:
    """Parse a supported date value into ``YYYY-MM-DD``.

    Returns ``None`` for empty or unsupported values. Callers decide whether
    that should become a warning.
    """

    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            continue

    return None
