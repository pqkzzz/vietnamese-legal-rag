"""Build parent-child retrieval chunks from normalized legal documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.legal_parser.point_splitter import (
    PointSplitResult,
    split_clause_points,
    strip_leading_clause_number,
    strip_leading_point_marker,
)
from app.utils.identifiers import make_point_chunk_id


@dataclass
class ChunkBuildIssue:
    """A warning or error emitted while building retrieval chunks."""

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
class ChunkBuildReport:
    """Counters and validation results for one normalized file."""

    law_id: str | None
    source_file: str
    output_file: str
    input_units: int = 0
    output_chunks: int = 0
    article_chunks: int = 0
    clause_chunks: int = 0
    parent_clause_chunks: int = 0
    point_chunks: int = 0
    article_leads_skipped: int = 0
    repealed_chunks: int = 0
    retrievable_chunks: int = 0
    non_retrievable_chunks: int = 0
    clauses_split: int = 0
    clauses_not_split: int = 0
    warnings: list[ChunkBuildIssue] = field(default_factory=list)
    errors: list[ChunkBuildIssue] = field(default_factory=list)

    def warn(self, unit_id: str | None, field: str, code: str, message: str) -> None:
        self.warnings.append(ChunkBuildIssue(unit_id, field, code, message))

    def error(self, unit_id: str | None, field: str, code: str, message: str) -> None:
        self.errors.append(ChunkBuildIssue(unit_id, field, code, message))

    def to_dict(self) -> dict[str, Any]:
        return {
            "law_id": self.law_id,
            "source_file": self.source_file,
            "output_file": self.output_file,
            "input_units": self.input_units,
            "output_chunks": self.output_chunks,
            "article_chunks": self.article_chunks,
            "clause_chunks": self.clause_chunks,
            "parent_clause_chunks": self.parent_clause_chunks,
            "point_chunks": self.point_chunks,
            "article_leads_skipped": self.article_leads_skipped,
            "repealed_chunks": self.repealed_chunks,
            "retrievable_chunks": self.retrievable_chunks,
            "non_retrievable_chunks": self.non_retrievable_chunks,
            "clauses_split": self.clauses_split,
            "clauses_not_split": self.clauses_not_split,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "warnings": [issue.to_dict() for issue in self.warnings],
            "errors": [issue.to_dict() for issue in self.errors],
        }


@dataclass
class ChunkBuildResult:
    """Retrieval chunks and report for one normalized document."""

    chunks: list[dict[str, Any]]
    report: ChunkBuildReport


def build_chunks_for_document(normalized_document: dict[str, Any], source_file: str) -> ChunkBuildResult:
    """Build retrieval chunks for one normalized legal document."""

    law_info = normalized_document.get("law_info")
    if not isinstance(law_info, dict):
        law_info = {}
    law_id = _string_or_none(law_info.get("law_id"))
    output_file = f"{law_id or source_file.removesuffix('_normalized.json')}_chunks.jsonl"
    units = normalized_document.get("legal_units")
    if not isinstance(units, list):
        units = []

    report = ChunkBuildReport(law_id=law_id, source_file=source_file, output_file=output_file, input_units=len(units))
    chunks: list[dict[str, Any]] = []

    for unit in units:
        if not isinstance(unit, dict):
            report.error(None, "legal_units", "INVALID_UNIT", "Normalized legal unit must be an object.")
            continue
        unit_type = unit.get("unit_type")
        if unit_type == "article_lead":
            report.article_leads_skipped += 1
            continue
        if unit_type == "article":
            chunk = _build_base_chunk(unit, law_info, "article")
            chunk["embedding_text"] = build_embedding_text(law_info, unit, "article")
            chunks.append(chunk)
            report.article_chunks += 1
            continue
        if unit_type == "clause":
            _add_clause_chunks(unit, law_info, chunks, report)
            continue
        if unit_type == "point":
            chunk = _build_base_chunk(unit, law_info, "point")
            chunk["embedding_text"] = build_embedding_text(law_info, unit, "point")
            chunks.append(chunk)
            report.point_chunks += 1
            continue
        report.error(_string_or_none(unit.get("unit_id")), "unit_type", "INVALID_UNIT_TYPE", f"Unsupported unit type: {unit_type}")

    _finalize_report_counts(chunks, report)
    _validate_chunks(chunks, report)
    report.output_chunks = len(chunks)
    return ChunkBuildResult(chunks=chunks, report=report)


def build_embedding_text(
    law_info: dict[str, Any],
    unit: dict[str, Any],
    chunk_type: str,
    clause_lead_clean: str | None = None,
) -> str:
    """Build deterministic embedding input text without creating vectors."""

    position = unit.get("position") if isinstance(unit.get("position"), dict) else {}
    lines = [
        _line("Văn bản", law_info.get("law_name")),
        _line("Số văn bản", law_info.get("document_number")),
        _article_line(position),
    ]
    if chunk_type in {"clause", "parent_clause"}:
        lines.append(_line(f"Khoản {position.get('clause_number')}", None))
        lines.append(_string_or_none(unit.get("content_clean")))
    elif chunk_type == "point":
        lead = strip_leading_clause_number(clause_lead_clean or _string_or_none(unit.get("clause_lead_clean")) or "")
        point_text = strip_leading_point_marker(_string_or_none(unit.get("content_clean")) or "")
        lines.append(_line(f"Khoản {position.get('clause_number')}", lead))
        lines.append(_line(f"Điểm {position.get('point_number')}", point_text))
    else:
        lines.append(_string_or_none(unit.get("content_clean")))
    return "\n".join(line for line in lines if line)


def _add_clause_chunks(
    unit: dict[str, Any],
    law_info: dict[str, Any],
    chunks: list[dict[str, Any]],
    report: ChunkBuildReport,
) -> None:
    split = split_clause_points(str(unit.get("content_raw") or ""), str(unit.get("content_clean") or ""))
    unit_id = _string_or_none(unit.get("unit_id"))
    for warning in split.warnings:
        report.warn(unit_id, warning.get("field") or "content_clean", warning.get("code") or "POINT_SPLIT_WARNING", warning.get("message") or "Point split warning.")

    if not split.was_split:
        chunk = _build_base_chunk(unit, law_info, "clause")
        chunk["embedding_text"] = build_embedding_text(law_info, unit, "clause")
        chunks.append(chunk)
        report.clause_chunks += 1
        report.clauses_not_split += 1
        return

    child_ids = [make_point_chunk_id(str(unit_id), point.point_number) for point in split.points]
    parent = _build_base_chunk(unit, law_info, "clause", has_children=True, child_ids=child_ids, is_retrievable=False)
    parent["embedding_text"] = build_embedding_text(law_info, unit, "parent_clause")
    parent["payload"]["clause_lead_raw"] = split.clause_lead_raw
    parent["payload"]["clause_lead_clean"] = split.clause_lead_clean
    chunks.append(parent)
    report.parent_clause_chunks += 1
    report.clauses_split += 1

    for point in split.points:
        point_unit = _point_unit_from_clause(unit, point.point_number, point.content_raw, point.content_clean)
        point_chunk = _build_base_chunk(
            point_unit,
            law_info,
            "point",
            parent_id=unit_id,
            has_children=False,
            child_ids=[],
            is_retrievable=bool(unit.get("is_retrievable")) and unit.get("provision_status") != "repealed",
        )
        point_chunk["chunk_id"] = make_point_chunk_id(str(unit_id), point.point_number)
        point_chunk["source_unit_id"] = unit_id
        point_chunk["payload"]["clause_lead_raw"] = split.clause_lead_raw
        point_chunk["payload"]["clause_lead_clean"] = split.clause_lead_clean
        point_chunk["embedding_text"] = build_embedding_text(law_info, point_unit, "point", split.clause_lead_clean)
        chunks.append(point_chunk)
        report.point_chunks += 1


def _build_base_chunk(
    unit: dict[str, Any],
    law_info: dict[str, Any],
    chunk_type: str,
    has_children: bool = False,
    child_ids: list[str] | None = None,
    parent_id: str | None = None,
    is_retrievable: bool | None = None,
) -> dict[str, Any]:
    unit_id = _string_or_none(unit.get("unit_id"))
    position = unit.get("position") if isinstance(unit.get("position"), dict) else {}
    payload = {
        "law_id": _string_or_none(law_info.get("law_id")),
        "law_name": _string_or_none(law_info.get("law_name")),
        "full_name": _string_or_none(law_info.get("full_name")),
        "document_number": _string_or_none(law_info.get("document_number")),
        "document_type": _string_or_none(law_info.get("document_type")),
        "document_status": _string_or_none(law_info.get("document_status")),
        "issue_date": _string_or_none(law_info.get("issue_date")),
        "effective_from": _string_or_none(law_info.get("effective_from")),
        "effective_to": _string_or_none(law_info.get("effective_to")),
        "chapter_number": _string_or_none(position.get("chapter_number")),
        "chapter_title": _string_or_none(position.get("chapter_title")),
        "section_number": _string_or_none(position.get("section_number")),
        "section_title": _string_or_none(position.get("section_title")),
        "article_number": _string_or_none(position.get("article_number")),
        "article_title": _string_or_none(position.get("article_title")),
        "clause_number": _string_or_none(position.get("clause_number")),
        "point_number": _string_or_none(position.get("point_number")),
        "article_id": _string_or_none(unit.get("article_id")),
        "parent_id": parent_id if parent_id is not None else _string_or_none(unit.get("parent_id")),
        "content_raw": unit.get("content_raw") if isinstance(unit.get("content_raw"), str) else str(unit.get("content_raw") or ""),
        "content_clean": unit.get("content_clean") if isinstance(unit.get("content_clean"), str) else str(unit.get("content_clean") or ""),
        "clause_lead_raw": _string_or_none(unit.get("clause_lead_raw")),
        "clause_lead_clean": _string_or_none(unit.get("clause_lead_clean")),
        "has_children": has_children,
        "child_ids": child_ids or [],
        "cross_references": unit.get("cross_references") if isinstance(unit.get("cross_references"), list) else [],
        "tags": unit.get("tags") if isinstance(unit.get("tags"), list) else [],
        "provision_status": _string_or_none(unit.get("provision_status")) or "effective",
        "is_retrievable": bool(unit.get("is_retrievable")) if is_retrievable is None else is_retrievable,
        "source": unit.get("source") if isinstance(unit.get("source"), dict) else {"source_file": None, "source_url": None},
    }
    return {
        "chunk_id": unit_id,
        "source_unit_id": _string_or_none(unit.get("source_unit_id")) or unit_id,
        "unit_type": chunk_type,
        "embedding_text": "",
        "payload": payload,
    }


def _point_unit_from_clause(unit: dict[str, Any], point_number: str, content_raw: str, content_clean: str) -> dict[str, Any]:
    position = dict(unit.get("position") if isinstance(unit.get("position"), dict) else {})
    position["point_number"] = point_number
    point_unit = dict(unit)
    point_unit["position"] = position
    point_unit["unit_type"] = "point"
    point_unit["content_raw"] = content_raw
    point_unit["content_clean"] = content_clean
    return point_unit


def _validate_chunks(chunks: list[dict[str, Any]], report: ChunkBuildReport) -> None:
    seen: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    children_by_parent: dict[str, list[str]] = {}

    for chunk in chunks:
        chunk_id = _string_or_none(chunk.get("chunk_id"))
        payload = chunk.get("payload") if isinstance(chunk.get("payload"), dict) else {}
        if not chunk_id:
            report.error(None, "chunk_id", "MISSING_CHUNK_ID", "Chunk is missing chunk_id.")
            continue
        if chunk_id in seen:
            report.error(chunk_id, "chunk_id", "DUPLICATE_CHUNK_ID", f"Duplicate chunk_id {chunk_id}.")
        seen.add(chunk_id)
        by_id[chunk_id] = chunk
        if chunk.get("unit_type") == "point":
            parent_id = _string_or_none(payload.get("parent_id"))
            if not parent_id:
                report.error(chunk_id, "parent_id", "MISSING_POINT_PARENT", "Point chunk is missing parent_id.")
            else:
                children_by_parent.setdefault(parent_id, []).append(chunk_id)
            if not payload.get("point_number"):
                report.error(chunk_id, "point_number", "MISSING_POINT_NUMBER", "Point chunk is missing point_number.")
            if not payload.get("article_id"):
                report.error(chunk_id, "article_id", "MISSING_ARTICLE_ID", "Point chunk is missing article_id.")
        if chunk.get("unit_type") == "article_lead":
            report.error(chunk_id, "unit_type", "ARTICLE_LEAD_CHUNK", "Article lead must not be emitted as retrieval chunk.")
        if payload.get("has_children") is False and chunk.get("unit_type") == "clause" and payload.get("child_ids"):
            report.error(chunk_id, "child_ids", "INVALID_CHILD_IDS", "Clause without children cannot list child_ids.")
        if payload.get("is_retrievable") and not chunk.get("embedding_text"):
            report.error(chunk_id, "embedding_text", "EMPTY_EMBEDDING_TEXT", "Retrievable chunk has empty embedding_text.")
        if not payload.get("content_raw") or not payload.get("content_clean"):
            report.error(chunk_id, "content", "EMPTY_CONTENT", "Chunk content_raw and content_clean must be present.")

    for parent_id, child_ids in children_by_parent.items():
        parent = by_id.get(parent_id)
        if parent is None:
            report.error(parent_id, "parent_id", "ORPHAN_POINT", "Point parent does not exist in output.")
            continue
        payload = parent.get("payload", {})
        if payload.get("has_children") is not True:
            report.error(parent_id, "has_children", "PARENT_HAS_CHILDREN_FALSE", "Parent with point children must have has_children=true.")
        if payload.get("child_ids") != child_ids:
            report.error(parent_id, "child_ids", "CHILD_IDS_MISMATCH", "Parent child_ids do not match emitted point children.")
        if payload.get("is_retrievable") is not False:
            report.error(parent_id, "is_retrievable", "PARENT_RETRIEVABLE", "Parent clause with point children must not be retrievable by default.")


def _finalize_report_counts(chunks: list[dict[str, Any]], report: ChunkBuildReport) -> None:
    for chunk in chunks:
        payload = chunk.get("payload") if isinstance(chunk.get("payload"), dict) else {}
        if payload.get("provision_status") == "repealed":
            report.repealed_chunks += 1
        if payload.get("is_retrievable") is True:
            report.retrievable_chunks += 1
        else:
            report.non_retrievable_chunks += 1


def _article_line(position: dict[str, Any]) -> str | None:
    article_number = _string_or_none(position.get("article_number"))
    article_title = _string_or_none(position.get("article_title"))
    if article_number and article_title:
        return f"Điều {article_number}: {article_title}"
    if article_number:
        return f"Điều {article_number}"
    return None


def _line(label: str, value: object) -> str | None:
    text = _string_or_none(value)
    if text:
        return f"{label}: {text}"
    if label and value is None and label.startswith("Khoản "):
        return label
    return None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

