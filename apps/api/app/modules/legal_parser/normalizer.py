"""Normalize raw Vietnamese legal JSON into a stable intermediate schema."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.dates import parse_date_to_iso
from app.utils.identifiers import make_article_id, parse_target_unit_id
from app.utils.text import (
    clean_legal_content,
    has_substantive_text,
    is_repealed_text,
    normalize_for_matching,
    strip_consolidated_suffix,
)

SCHEMA_VERSION = "1.0"
VALID_UNIT_TYPES = {"article", "article_lead", "clause", "point"}


@dataclass
class NormalizationIssue:
    """A warning or error emitted while normalizing one file."""

    unit_id: str | None
    field: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "unit_id": self.unit_id,
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class NormalizationContext:
    """Mutable per-file report state."""

    source_file: str
    warnings: list[NormalizationIssue] = field(default_factory=list)
    errors: list[NormalizationIssue] = field(default_factory=list)

    def warn(self, unit_id: str | None, field: str, code: str, message: str) -> None:
        self.warnings.append(NormalizationIssue(unit_id, field, code, message))

    def error(self, unit_id: str | None, field: str, code: str, message: str) -> None:
        self.errors.append(NormalizationIssue(unit_id, field, code, message))


def normalize_document(raw_document: dict[str, Any], source_file: str) -> dict[str, Any]:
    """Normalize one raw legal document into schema version 1.0."""

    context = NormalizationContext(source_file=source_file)
    raw_law_info = raw_document.get("law_info")
    if not isinstance(raw_law_info, dict):
        raw_law_info = {}
        context.error(None, "law_info", "INVALID_LAW_INFO", "law_info must be an object")

    law_id = _string_or_none(raw_law_info.get("law_id")) or ""
    clauses = raw_document.get("clauses", [])
    if not isinstance(clauses, list):
        context.error(None, "clauses", "INVALID_CLAUSES", "clauses must be a list")
        clauses = []

    law_info = _normalize_law_info(raw_law_info, context)
    legal_units: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw_unit in enumerate(clauses):
        unit = _normalize_unit(raw_unit, index, law_id, source_file, context, seen_ids)
        if unit is not None:
            legal_units.append(unit)

    return {
        "schema_version": SCHEMA_VERSION,
        "law_info": law_info,
        "legal_units": legal_units,
        "normalization_report": {
            "source_file": source_file,
            "total_input_units": len(clauses),
            "total_output_units": len(legal_units),
            "valid_units": len(legal_units),
            "warning_count": len(context.warnings),
            "error_count": len(context.errors),
            "warnings": [issue.to_dict() for issue in context.warnings],
            "errors": [issue.to_dict() for issue in context.errors],
        },
    }


def normalize_file(input_path: Path) -> dict[str, Any]:
    """Read and normalize one JSON file from disk."""

    import json

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{input_path} must contain a JSON object")
    return normalize_document(raw, input_path.name)


def output_filename_for(normalized_document: dict[str, Any], fallback_stem: str) -> str:
    """Return the normalized output filename for a document."""

    law_id = normalized_document.get("law_info", {}).get("law_id")
    return f"{law_id or fallback_stem}_normalized.json"


def _normalize_law_info(raw: dict[str, Any], context: NormalizationContext) -> dict[str, Any]:
    law_id = _string_or_none(raw.get("law_id"))
    full_name = _string_or_none(raw.get("law_name"))
    document_number = _string_or_none(raw.get("document_number"))

    issue_date = _parse_date_field(raw, "issue_date", context)
    effective_from = _parse_date_field(raw, "effective_date", context)
    effective_to = _parse_date_field(raw, "effective_to", context)

    status = _normalize_status(raw.get("status"))
    if status == "unknown" and raw.get("status") not in (None, ""):
        context.warn(None, "status", "UNKNOWN_STATUS", f"Unrecognized document status: {raw.get('status')}")

    return {
        "law_id": law_id,
        "law_name": strip_consolidated_suffix(full_name) if full_name else None,
        "full_name": full_name,
        "publisher": _string_or_none(raw.get("publisher")),
        "document_number": document_number,
        "document_type": _detect_document_type(full_name, document_number),
        "issue_date": issue_date,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "document_status": status,
        "executive_summary": _string_or_none(raw.get("executive_summary")),
    }


def _normalize_unit(
    raw_unit: Any,
    index: int,
    law_id: str,
    source_file: str,
    context: NormalizationContext,
    seen_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(raw_unit, dict):
        context.error(None, f"clauses[{index}]", "INVALID_UNIT", "Unit must be an object")
        return None

    unit_id = _string_or_none(raw_unit.get("id"))
    if not unit_id:
        context.error(None, "id", "MISSING_UNIT_ID", "Unit is missing id")
        return None
    if unit_id in seen_ids:
        context.error(unit_id, "id", "DUPLICATE_UNIT_ID", f"Duplicate unit id {unit_id}")
        return None
    seen_ids.add(unit_id)

    if not law_id:
        context.error(unit_id, "law_id", "MISSING_LAW_ID", "Document is missing law_id")
        return None

    position = raw_unit.get("position")
    if not isinstance(position, dict):
        context.error(unit_id, "position", "INVALID_POSITION", "position must be an object")
        return None

    article_number = _position_value(position.get("article"))
    if article_number is None:
        context.error(unit_id, "position.article", "MISSING_ARTICLE_NUMBER", "Unit is missing article number")
        return None

    content_raw = _content_to_string(raw_unit.get("content"))
    if content_raw is None:
        context.error(unit_id, "content", "INVALID_CONTENT", "Content must be convertible to a string")
        return None

    chapter_number = _position_value(position.get("chapter"))
    if chapter_number is None:
        context.warn(unit_id, "position.chapter", "MISSING_CHAPTER", "Unit is missing chapter number")

    unit_type = _unit_type(position)
    clause_number = None if unit_type == "article_lead" else _position_value(position.get("clause"))
    point_number = _position_value(position.get("point"))
    article_id = make_article_id(law_id, article_number)
    parent_id = _parent_id(unit_type, article_id, law_id, article_number, clause_number, point_number, context, unit_id)
    content_clean = clean_legal_content(content_raw)
    provision_status = "repealed" if is_repealed_text(content_clean) else "effective"

    normalized = {
        "unit_id": unit_id,
        "source_unit_id": unit_id,
        "unit_type": unit_type,
        "position": {
            "chapter_number": chapter_number,
            "chapter_title": _position_value(position.get("chapter_title")),
            "section_number": _position_value(position.get("section")),
            "section_title": _position_value(position.get("section_title")),
            "article_number": article_number,
            "article_title": _position_value(position.get("article_title")),
            "clause_number": clause_number,
            "point_number": point_number,
        },
        "article_id": article_id,
        "parent_id": parent_id,
        "content_raw": content_raw,
        "content_clean": content_clean,
        "cross_references": _normalize_cross_references(raw_unit.get("cross_references"), law_id, context, unit_id),
        "tags": _normalize_tags(raw_unit.get("tags"), context, unit_id),
        "provision_status": provision_status,
        "is_retrievable": _is_retrievable(unit_type, provision_status, content_clean),
        "source": {"source_file": source_file, "source_url": _string_or_none(raw_unit.get("source_url"))},
    }

    _validate_normalized_unit(normalized, context)
    return normalized


def _parse_date_field(raw: dict[str, Any], field_name: str, context: NormalizationContext) -> str | None:
    value = raw.get(field_name)
    parsed = parse_date_to_iso(value)
    if parsed is None and value not in (None, ""):
        context.warn(None, field_name, "INVALID_DATE", f"Cannot parse date {value}")
    return parsed


def _normalize_status(value: object) -> str:
    mapping = {
        "đang có hiệu lực": "effective",
        "hết hiệu lực": "expired",
        "chưa có hiệu lực": "not_yet_effective",
        "bị bãi bỏ": "repealed",
    }
    return mapping.get(normalize_for_matching(value), "unknown")


def _detect_document_type(full_name: str | None, document_number: str | None) -> str | None:
    haystack = normalize_for_matching(f"{full_name or ''} {document_number or ''}")
    if "văn bản hợp nhất" in haystack or "vbhn" in haystack:
        return "Văn bản hợp nhất"
    return None


def _unit_type(position: dict[str, Any]) -> str:
    if position.get("point") is not None:
        return "point"
    clause = position.get("clause")
    if clause is None:
        return "article"
    if str(clause).strip() == "0":
        return "article_lead"
    return "clause"


def _parent_id(
    unit_type: str,
    article_id: str,
    law_id: str,
    article_number: str,
    clause_number: str | None,
    point_number: str | None,
    context: NormalizationContext,
    unit_id: str,
) -> str | None:
    if unit_type == "article":
        return None
    if unit_type in {"article_lead", "clause"}:
        return article_id
    if unit_type == "point" and clause_number:
        return f"{law_id}_D{article_number}_K{clause_number}"
    if unit_type == "point" and point_number:
        context.warn(unit_id, "parent_id", "MISSING_PARENT", "Cannot determine parent clause for point")
    return None


def _normalize_tags(raw_tags: Any, context: NormalizationContext, unit_id: str) -> list[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, list):
        values = raw_tags
    elif isinstance(raw_tags, str):
        context.warn(unit_id, "tags", "INVALID_TAGS_TYPE", "Tags was a string; converted to a single-item list")
        values = [raw_tags]
    else:
        context.warn(unit_id, "tags", "INVALID_TAGS_TYPE", "Tags was not a list; converted values where possible")
        values = [raw_tags]

    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value).strip()
        if not tag:
            continue
        key = tag.casefold()
        if key not in seen:
            seen.add(key)
            result.append(tag)
    return result


def _normalize_cross_references(
    raw_references: Any,
    law_id: str,
    context: NormalizationContext,
    unit_id: str,
) -> list[dict[str, Any]]:
    if raw_references is None:
        return []
    if not isinstance(raw_references, list):
        context.warn(unit_id, "cross_references", "INVALID_CROSS_REFERENCES", "cross_references was not a list")
        raw_references = [raw_references]

    references: list[dict[str, Any]] = []
    for raw_reference in raw_references:
        try:
            references.append(_normalize_cross_reference(raw_reference, law_id, context, unit_id))
        except (TypeError, ValueError) as exc:
            context.warn(unit_id, "cross_references", "INVALID_CROSS_REFERENCE", str(exc))
    return references


def _normalize_cross_reference(
    raw_reference: Any,
    law_id: str,
    context: NormalizationContext,
    unit_id: str,
) -> dict[str, Any]:
    if isinstance(raw_reference, str):
        return {
            "reference_type": "unknown",
            "target_law_id": None,
            "target_article_number": None,
            "target_clause_number": None,
            "target_point_number": None,
            "target_unit_id": None,
            "anchor_text": raw_reference,
            "description_summary": None,
            "raw_reference": raw_reference,
        }
    if not isinstance(raw_reference, dict):
        raise TypeError("Cross-reference must be an object or string")

    target_unit_id = _string_or_none(raw_reference.get("target_unit_id") or raw_reference.get("target_id"))
    parsed = parse_target_unit_id(target_unit_id)
    target_law_id = _first_string(raw_reference, ("target_law_id", "law_id", "target_law"), parsed["target_law_id"])
    target_article_number = _first_string(raw_reference, ("target_article_number", "article_number", "article"), parsed["target_article_number"])
    target_clause_number = _first_string(raw_reference, ("target_clause_number", "clause_number", "clause"), parsed["target_clause_number"])
    target_point_number = _first_string(raw_reference, ("target_point_number", "point_number", "point"), parsed["target_point_number"])

    reference_type = _string_or_none(raw_reference.get("reference_type"))
    if reference_type not in {"internal", "external", "unknown"}:
        if target_law_id == law_id:
            reference_type = "internal"
        elif target_law_id:
            reference_type = "external"
        else:
            reference_type = "unknown"
    if reference_type == "unknown" and not target_unit_id:
        context.warn(unit_id, "cross_references", "MISSING_REFERENCE_TARGET", "Cross-reference is missing target")

    return {
        "reference_type": reference_type,
        "target_law_id": target_law_id,
        "target_article_number": target_article_number,
        "target_clause_number": target_clause_number,
        "target_point_number": target_point_number,
        "target_unit_id": target_unit_id,
        "anchor_text": _string_or_none(raw_reference.get("anchor_text")),
        "description_summary": _string_or_none(raw_reference.get("description_summary")),
        "raw_reference": deepcopy(raw_reference),
    }


def _validate_normalized_unit(unit: dict[str, Any], context: NormalizationContext) -> None:
    unit_id = unit.get("unit_id")
    if unit.get("unit_type") not in VALID_UNIT_TYPES:
        context.error(unit_id, "unit_type", "INVALID_UNIT_TYPE", f"Invalid unit type {unit.get('unit_type')}")
    for field_name, value in unit.get("position", {}).items():
        if value is not None and not isinstance(value, str):
            context.error(unit_id, f"position.{field_name}", "INVALID_POSITION_TYPE", "Position fields must be strings or null")
    if not isinstance(unit.get("is_retrievable"), bool):
        context.error(unit_id, "is_retrievable", "INVALID_RETRIEVABLE", "is_retrievable must be boolean")
    if not isinstance(unit.get("tags"), list) or not all(isinstance(tag, str) for tag in unit["tags"]):
        context.error(unit_id, "tags", "INVALID_TAGS", "tags must be a list of strings")
    if not isinstance(unit.get("cross_references"), list):
        context.error(unit_id, "cross_references", "INVALID_CROSS_REFERENCES", "cross_references must be a list")


def _is_retrievable(unit_type: str, provision_status: str, content_clean: str) -> bool:
    if unit_type == "article_lead" or provision_status == "repealed":
        return False
    return unit_type in {"article", "clause"} and has_substantive_text(content_clean)


def _position_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return text or None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _content_to_string(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    return value if isinstance(value, str) else str(value)


def _first_string(raw: dict[str, Any], keys: tuple[str, ...], fallback: str | None) -> str | None:
    for key in keys:
        value = _position_value(raw.get(key))
        if value is not None:
            return value
    return fallback
