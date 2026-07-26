"""Build an in-memory legal provision hierarchy from retrieval JSONL chunks."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.modules.evidence.models import (
    HierarchyBuildReport,
    HierarchyWarning,
    ProvisionLevel,
    ProvisionLocation,
    ProvisionLookupResult,
    ProvisionNode,
)


class LegalProvisionHierarchyIndex:
    """In-memory hierarchy index for legal retrieval chunks."""

    def __init__(
        self,
        *,
        nodes_by_id: dict[str, ProvisionNode],
        nodes_by_location: dict[tuple[ProvisionLevel, ProvisionLocation], list[ProvisionNode]],
        children_by_parent: dict[str, list[ProvisionNode]],
        nodes_by_article: dict[tuple[str, str], list[ProvisionNode]],
        nodes_by_clause: dict[tuple[str, str, str], list[ProvisionNode]],
        warnings: list[HierarchyWarning],
        build_report: HierarchyBuildReport,
    ) -> None:
        self.nodes_by_id = nodes_by_id
        self.nodes_by_location = nodes_by_location
        self.children_by_parent = children_by_parent
        self.nodes_by_article = nodes_by_article
        self.nodes_by_clause = nodes_by_clause
        self.warnings = warnings
        self.build_report = build_report

    @classmethod
    def from_jsonl_directory(cls, path: str | Path, *, strict: bool = False) -> "LegalProvisionHierarchyIndex":
        directory = Path(path)
        if not directory.exists():
            raise FileNotFoundError(f"Hierarchy source directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Hierarchy source path is not a directory: {directory}")

        jsonl_files = sorted(directory.glob("*_chunks.jsonl"), key=lambda item: item.name)
        nodes_by_id: dict[str, ProvisionNode] = {}
        source_files: list[str] = []
        warnings: list[HierarchyWarning] = []
        total_records = 0
        duplicate_chunk_ids = 0
        order_index = 0

        for jsonl_file in jsonl_files:
            source_files.append(str(jsonl_file))
            with jsonl_file.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    total_records += 1
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        warning = HierarchyWarning(
                            code="INVALID_JSON",
                            message=str(exc),
                            source_file=str(jsonl_file),
                            line_number=line_number,
                        )
                        warnings.append(warning)
                        if strict:
                            raise ValueError(warning.message) from exc
                        continue

                    node = _node_from_record(record, order_index, str(jsonl_file), line_number, warnings)
                    order_index += 1
                    if node is None:
                        continue
                    if node.chunk_id in nodes_by_id:
                        duplicate_chunk_ids += 1
                        warning = HierarchyWarning(
                            code="DUPLICATE_CHUNK_ID",
                            message="Duplicate chunk_id encountered; keeping the first record.",
                            chunk_id=node.chunk_id,
                            source_file=str(jsonl_file),
                            line_number=line_number,
                            details={"policy": "keep_first"},
                        )
                        warnings.append(warning)
                        if strict:
                            raise ValueError(warning.message)
                        continue
                    nodes_by_id[node.chunk_id] = node

        indexes = _build_secondary_indexes(nodes_by_id, warnings, strict=strict)
        _assign_sibling_links(nodes_by_id, indexes["children_by_parent"], indexes["nodes_by_article"])
        duplicate_locations = sum(1 for warning in warnings if warning.code == "DUPLICATE_LOCATION")
        orphan_nodes = sum(1 for warning in warnings if warning.code == "ORPHAN_PARENT")
        build_report = HierarchyBuildReport(
            source_files=source_files,
            total_records=total_records,
            total_nodes=len(nodes_by_id),
            article_nodes=sum(1 for node in nodes_by_id.values() if node.level == ProvisionLevel.ARTICLE),
            clause_nodes=sum(1 for node in nodes_by_id.values() if node.level == ProvisionLevel.CLAUSE),
            point_nodes=sum(1 for node in nodes_by_id.values() if node.level == ProvisionLevel.POINT),
            retrievable_nodes=sum(1 for node in nodes_by_id.values() if node.is_retrievable),
            non_retrievable_nodes=sum(1 for node in nodes_by_id.values() if not node.is_retrievable),
            orphan_nodes=orphan_nodes,
            duplicate_chunk_ids=duplicate_chunk_ids,
            duplicate_locations=duplicate_locations,
            warning_count=len(warnings),
            warnings=warnings,
        )
        return cls(
            nodes_by_id=nodes_by_id,
            nodes_by_location=indexes["nodes_by_location"],
            children_by_parent=indexes["children_by_parent"],
            nodes_by_article=indexes["nodes_by_article"],
            nodes_by_clause=indexes["nodes_by_clause"],
            warnings=warnings,
            build_report=build_report,
        )

    def get_node(self, chunk_id: str) -> ProvisionNode | None:
        return self.nodes_by_id.get(chunk_id)

    def get_parent(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or not node.parent_id:
            return None
        return self.nodes_by_id.get(node.parent_id)

    def get_children(self, chunk_id: str) -> list[ProvisionNode]:
        node = self.get_node(chunk_id)
        if node is None:
            return []
        ordered_children: list[ProvisionNode] = []
        seen: set[str] = set()
        for child_id in node.child_ids:
            child = self.nodes_by_id.get(child_id)
            if child is not None:
                ordered_children.append(child)
                seen.add(child.chunk_id)
        for child in self.children_by_parent.get(chunk_id, []):
            if child.chunk_id not in seen:
                ordered_children.append(child)
                seen.add(child.chunk_id)
        return ordered_children

    def get_siblings(self, chunk_id: str) -> list[ProvisionNode]:
        node = self.get_node(chunk_id)
        if node is None:
            return []
        return [sibling for sibling in self._sibling_group(node) if sibling.chunk_id != chunk_id]

    def get_previous_sibling(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or node.previous_sibling_id is None:
            return None
        return self.nodes_by_id.get(node.previous_sibling_id)

    def get_next_sibling(self, chunk_id: str) -> ProvisionNode | None:
        node = self.get_node(chunk_id)
        if node is None or node.next_sibling_id is None:
            return None
        return self.nodes_by_id.get(node.next_sibling_id)

    def lookup(
        self,
        law_id: str,
        article_number: str,
        clause_number: str | None = None,
        point_number: str | None = None,
    ) -> ProvisionLookupResult:
        location = ProvisionLocation(
            law_id=law_id,
            article_number=article_number,
            clause_number=clause_number,
            point_number=point_number,
        )
        warnings: list[str] = []

        if point_number is not None:
            exact = self._first_location_node(ProvisionLevel.POINT, location)
            nodes = [exact] if exact is not None else []
            return ProvisionLookupResult(
                location=location,
                exact_node=exact,
                nodes=nodes,
                matched_level=ProvisionLevel.POINT if exact else None,
                found=exact is not None,
                warnings=warnings,
            )

        if clause_number is not None:
            nodes = self._ordered_clause_lookup(law_id, article_number, clause_number)
            exact = next((node for node in nodes if node.level == ProvisionLevel.CLAUSE), None)
            return ProvisionLookupResult(
                location=location,
                exact_node=exact,
                nodes=nodes,
                matched_level=ProvisionLevel.CLAUSE if nodes else None,
                found=bool(nodes),
                warnings=warnings,
            )

        nodes = self.get_article_nodes(law_id, article_number)
        exact = next((node for node in nodes if node.level == ProvisionLevel.ARTICLE), None)
        return ProvisionLookupResult(
            location=location,
            exact_node=exact,
            nodes=nodes,
            matched_level=ProvisionLevel.ARTICLE if nodes else None,
            found=bool(nodes),
            warnings=warnings,
        )

    def get_article_nodes(self, law_id: str, article_number: str) -> list[ProvisionNode]:
        return list(self.nodes_by_article.get((law_id, article_number), []))

    def get_clause_nodes(self, law_id: str, article_number: str, clause_number: str) -> list[ProvisionNode]:
        return list(self.nodes_by_clause.get((law_id, article_number, clause_number), []))

    def get_build_report(self) -> HierarchyBuildReport:
        return self.build_report

    def _first_location_node(self, level: ProvisionLevel, location: ProvisionLocation) -> ProvisionNode | None:
        nodes = self.nodes_by_location.get((level, location), [])
        return nodes[0] if nodes else None

    def _ordered_clause_lookup(self, law_id: str, article_number: str, clause_number: str) -> list[ProvisionNode]:
        clause_nodes = self.get_clause_nodes(law_id, article_number, clause_number)
        parent_clause = next((node for node in clause_nodes if node.level == ProvisionLevel.CLAUSE), None)
        if parent_clause is None:
            return clause_nodes
        nodes = [parent_clause]
        child_ids = parent_clause.child_ids
        if child_ids:
            children = self.get_children(parent_clause.chunk_id)
            nodes.extend(child for child in children if child.level == ProvisionLevel.POINT)
            return nodes
        nodes.extend(node for node in clause_nodes if node.level == ProvisionLevel.POINT)
        return nodes

    def _sibling_group(self, node: ProvisionNode) -> list[ProvisionNode]:
        if node.level == ProvisionLevel.POINT and node.parent_id:
            parent = self.nodes_by_id.get(node.parent_id)
            if parent is not None:
                return [child for child in self.get_children(parent.chunk_id) if child.level == ProvisionLevel.POINT]
            return [child for child in self.children_by_parent.get(node.parent_id, []) if child.level == ProvisionLevel.POINT]
        if node.level == ProvisionLevel.CLAUSE and node.law_id and node.article_number:
            article_nodes = self.nodes_by_article.get((node.law_id, node.article_number), [])
            return [item for item in article_nodes if item.level == ProvisionLevel.CLAUSE]
        return []


def _build_secondary_indexes(
    nodes_by_id: dict[str, ProvisionNode],
    warnings: list[HierarchyWarning],
    *,
    strict: bool,
) -> dict[str, Any]:
    nodes_by_location: dict[tuple[ProvisionLevel, ProvisionLocation], list[ProvisionNode]] = {}
    children_by_parent: dict[str, list[ProvisionNode]] = {}
    nodes_by_article: dict[tuple[str, str], list[ProvisionNode]] = {}
    nodes_by_clause: dict[tuple[str, str, str], list[ProvisionNode]] = {}

    for node in sorted(nodes_by_id.values(), key=lambda item: item.order_index):
        if node.parent_id:
            children_by_parent.setdefault(node.parent_id, []).append(node)
        if node.article_number:
            nodes_by_article.setdefault((node.law_id, node.article_number), []).append(node)
        if node.article_number and node.clause_number:
            nodes_by_clause.setdefault((node.law_id, node.article_number, node.clause_number), []).append(node)
        location = node.location
        location_key = (node.level, location)
        existing = nodes_by_location.setdefault(location_key, [])
        if existing:
            warning = HierarchyWarning(
                code="DUPLICATE_LOCATION",
                message="Duplicate legal location encountered for the same level.",
                chunk_id=node.chunk_id,
                related_chunk_id=existing[0].chunk_id,
                details={"level": node.level.value, "location": location.__dict__},
            )
            warnings.append(warning)
            if strict:
                raise ValueError(warning.message)
        existing.append(node)

    _validate_relationships(nodes_by_id, children_by_parent, warnings, strict=strict)
    for mapping in (children_by_parent, nodes_by_article, nodes_by_clause):
        for key, values in mapping.items():
            mapping[key] = sorted(values, key=lambda item: item.order_index)

    return {
        "nodes_by_location": nodes_by_location,
        "children_by_parent": children_by_parent,
        "nodes_by_article": nodes_by_article,
        "nodes_by_clause": nodes_by_clause,
    }


def _validate_relationships(
    nodes_by_id: dict[str, ProvisionNode],
    children_by_parent: dict[str, list[ProvisionNode]],
    warnings: list[HierarchyWarning],
    *,
    strict: bool,
) -> None:
    for node in nodes_by_id.values():
        if node.level == ProvisionLevel.UNKNOWN:
            _warn(warnings, "INVALID_LEVEL", "unit_type does not map to a known provision level.", node, strict=strict)
        if not node.content_clean.strip():
            _warn(warnings, "MISSING_CONTENT", "Node content_clean is empty.", node, strict=strict)
        if node.parent_id:
            parent = nodes_by_id.get(node.parent_id)
            if parent is None:
                if _is_virtual_article_parent(node):
                    continue
                if _parent_id_looks_cross_law(node):
                    _warn(
                        warnings,
                        "CROSS_LAW_PARENT",
                        "Node parent_id appears to belong to a different law_id.",
                        node,
                        related_chunk_id=node.parent_id,
                        strict=strict,
                    )
                _warn(warnings, "ORPHAN_PARENT", "Node parent_id does not exist in the hierarchy.", node, strict=strict)
            elif parent.law_id != node.law_id:
                _warn(
                    warnings,
                    "CROSS_LAW_PARENT",
                    "Node parent belongs to a different law_id.",
                    node,
                    related_chunk_id=parent.chunk_id,
                    strict=strict,
                )

    for parent in nodes_by_id.values():
        for child_id in parent.child_ids:
            child = nodes_by_id.get(child_id)
            if child is None:
                _warn(
                    warnings,
                    "MISSING_CHILD",
                    "Parent child_ids contains a missing child.",
                    parent,
                    related_chunk_id=child_id,
                    strict=strict,
                )
                continue
            if child.parent_id != parent.chunk_id:
                _warn(
                    warnings,
                    "PARENT_CHILD_MISMATCH",
                    "Parent child_ids contains a child whose parent_id does not point back.",
                    parent,
                    related_chunk_id=child.chunk_id,
                    strict=strict,
                )

    for parent_id, children in children_by_parent.items():
        parent = nodes_by_id.get(parent_id)
        if parent is None:
            continue
        if parent.child_ids:
            declared = set(parent.child_ids)
            for child in children:
                if child.chunk_id not in declared:
                    _warn(
                        warnings,
                        "PARENT_CHILD_MISMATCH",
                        "Child parent_id points to parent but parent child_ids does not contain child.",
                        child,
                        related_chunk_id=parent.chunk_id,
                        strict=strict,
                    )


def _is_virtual_article_parent(node: ProvisionNode) -> bool:
    """Return True for a clause pointing at its non-emitted article container."""

    if node.level != ProvisionLevel.CLAUSE:
        return False
    if not node.article_id or not node.parent_id or not node.article_number:
        return False
    if node.parent_id != node.article_id:
        return False
    return node.article_id == f"{node.law_id}_D{node.article_number}"


def _parent_id_looks_cross_law(node: ProvisionNode) -> bool:
    if not node.parent_id or not node.law_id:
        return False
    return not node.parent_id.startswith(f"{node.law_id}_")


def _assign_sibling_links(
    nodes_by_id: dict[str, ProvisionNode],
    children_by_parent: dict[str, list[ProvisionNode]],
    nodes_by_article: dict[tuple[str, str], list[ProvisionNode]],
) -> None:
    sibling_groups: list[list[ProvisionNode]] = []
    for parent_id, children in children_by_parent.items():
        parent = nodes_by_id.get(parent_id)
        if parent is not None and parent.child_ids:
            sibling_groups.append([child for child in _ordered_children(parent, children, nodes_by_id) if child.level == ProvisionLevel.POINT])
        else:
            sibling_groups.append([child for child in sorted(children, key=lambda item: item.order_index) if child.level == ProvisionLevel.POINT])
    for article_nodes in nodes_by_article.values():
        sibling_groups.append([node for node in article_nodes if node.level == ProvisionLevel.CLAUSE])

    for group in sibling_groups:
        for index, node in enumerate(group):
            node.previous_sibling_id = group[index - 1].chunk_id if index > 0 else None
            node.next_sibling_id = group[index + 1].chunk_id if index + 1 < len(group) else None


def _ordered_children(parent: ProvisionNode, children: list[ProvisionNode], nodes_by_id: dict[str, ProvisionNode]) -> list[ProvisionNode]:
    ordered: list[ProvisionNode] = []
    seen: set[str] = set()
    for child_id in parent.child_ids:
        child = nodes_by_id.get(child_id)
        if child is not None:
            ordered.append(child)
            seen.add(child.chunk_id)
    for child in sorted(children, key=lambda item: item.order_index):
        if child.chunk_id not in seen:
            ordered.append(child)
    return ordered


def _node_from_record(
    record: Any,
    order_index: int,
    source_file: str,
    line_number: int,
    warnings: list[HierarchyWarning],
) -> ProvisionNode | None:
    if not isinstance(record, dict):
        warnings.append(
            HierarchyWarning(
                code="INVALID_RECORD",
                message="JSONL record is not an object.",
                source_file=source_file,
                line_number=line_number,
            )
        )
        return None

    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    chunk_id = _string_or_none(record.get("chunk_id") or payload.get("chunk_id"))
    if chunk_id is None:
        warnings.append(
            HierarchyWarning(
                code="MISSING_CHUNK_ID",
                message="Record is missing chunk_id.",
                source_file=source_file,
                line_number=line_number,
            )
        )
        return None

    unit_type = _string_or_none(record.get("unit_type") or payload.get("unit_type")) or "unknown"
    level = _level_from_unit_type(unit_type)
    content_clean = _string_or_none(payload.get("content_clean")) or ""
    return ProvisionNode(
        qdrant_point_id=None,
        chunk_id=chunk_id,
        source_unit_id=_string_or_none(record.get("source_unit_id") or payload.get("source_unit_id")),
        unit_type=unit_type,
        level=level,
        law_id=_string_or_none(payload.get("law_id")) or "",
        law_name=_string_or_none(payload.get("law_name")),
        chapter_number=_string_or_none(payload.get("chapter_number")),
        chapter_title=_string_or_none(payload.get("chapter_title")),
        section_number=_string_or_none(payload.get("section_number")),
        section_title=_string_or_none(payload.get("section_title")),
        article_number=_string_or_none(payload.get("article_number")),
        article_title=_string_or_none(payload.get("article_title")),
        clause_number=_string_or_none(payload.get("clause_number")),
        point_number=_string_or_none(payload.get("point_number")),
        article_id=_string_or_none(payload.get("article_id")),
        parent_id=_string_or_none(payload.get("parent_id")),
        child_ids=_string_tuple(payload.get("child_ids")),
        has_children=bool(payload.get("has_children")),
        content_raw=_string_or_none(payload.get("content_raw")),
        content_clean=content_clean,
        clause_lead_raw=_string_or_none(payload.get("clause_lead_raw")),
        clause_lead_clean=_string_or_none(payload.get("clause_lead_clean")),
        cross_references=_dict_list(payload.get("cross_references")),
        tags=_string_list(payload.get("tags")),
        provision_status=_string_or_none(payload.get("provision_status")),
        is_retrievable=bool(payload.get("is_retrievable")),
        document_status=_string_or_none(payload.get("document_status")),
        order_index=order_index,
        previous_sibling_id=None,
        next_sibling_id=None,
        metadata=deepcopy(record),
    )


def _level_from_unit_type(unit_type: str) -> ProvisionLevel:
    if unit_type == "article":
        return ProvisionLevel.ARTICLE
    if unit_type == "clause":
        return ProvisionLevel.CLAUSE
    if unit_type == "point":
        return ProvisionLevel.POINT
    return ProvisionLevel.UNKNOWN


def _warn(
    warnings: list[HierarchyWarning],
    code: str,
    message: str,
    node: ProvisionNode,
    *,
    related_chunk_id: str | None = None,
    strict: bool,
) -> None:
    warning = HierarchyWarning(
        code=code,
        message=message,
        chunk_id=node.chunk_id,
        related_chunk_id=related_chunk_id,
    )
    warnings.append(warning)
    if strict:
        raise ValueError(message)


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in (_string_or_none(item) for item in value) if item is not None)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in (_string_or_none(item) for item in value) if item is not None]


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [deepcopy(item) for item in value if isinstance(item, dict)]

