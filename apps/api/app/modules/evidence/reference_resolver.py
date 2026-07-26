"""Resolve parsed legal references against the provision hierarchy."""

from __future__ import annotations

from app.modules.evidence.hierarchy_index import LegalProvisionHierarchyIndex
from app.modules.evidence.models import (
    LegalReference,
    LegalReferenceType,
    ProvisionNode,
    ReferenceResolutionBatch,
    ReferenceResolutionStatus,
    ResolvedLegalReference,
)
from app.modules.evidence.reference_parser import LegalReferenceParser
from app.utils.identifiers import parse_target_unit_id


class LegalReferenceResolver:
    """Resolve direct references without traversing the reference graph.

    Clause and article citations can resolve to multiple physical chunks, but
    they are still marked resolved_exact when the legal location is precise.
    Evidence expansion decides later whether and how to follow those targets.
    """

    def __init__(self, hierarchy: LegalProvisionHierarchyIndex, parser: LegalReferenceParser | None = None) -> None:
        self.hierarchy = hierarchy
        self.parser = parser or LegalReferenceParser()

    def resolve(self, reference: LegalReference) -> ResolvedLegalReference:
        warnings: list[str] = []
        source_node = self.hierarchy.get_node(reference.source_chunk_id)
        law_id = self._target_law_id(reference, source_node)
        article = reference.target_article_number
        clause = reference.target_clause_number
        point = reference.target_point_number

        if reference.target_unit_id:
            node = self.hierarchy.get_node(reference.target_unit_id)
            if node is not None:
                warnings.extend(_node_location_warnings(reference, node))
                return ResolvedLegalReference(
                    reference=reference,
                    status=ReferenceResolutionStatus.RESOLVED_EXACT,
                    resolved_nodes=[node],
                    exact_node=node,
                    warnings=warnings,
                )

            parsed_id = parse_target_unit_id(reference.target_unit_id)
            law_id = law_id or parsed_id["target_law_id"]
            article = article or parsed_id["target_article_number"]
            clause = clause or parsed_id["target_clause_number"]
            point = point or parsed_id["target_point_number"]
            warnings.append("target_unit_id was not found; attempted location fallback.")

        if law_id is None:
            if reference.reference_type == LegalReferenceType.EXTERNAL:
                return _unresolved(reference, warnings + ["External reference is missing target_law_id."])
            return _unresolved(reference, warnings + ["Reference is missing target_law_id."])

        if article is None:
            return _unresolved(reference, warnings + ["Reference is missing target_article_number."])

        lookup = self.hierarchy.lookup(law_id, article, clause, point)
        warnings.extend(lookup.warnings)
        if not lookup.found:
            return _unresolved(reference, warnings + ["Target location was not found in hierarchy."])

        status = ReferenceResolutionStatus.RESOLVED_EXACT
        return ResolvedLegalReference(
            reference=reference,
            status=status,
            resolved_nodes=lookup.nodes,
            exact_node=lookup.exact_node,
            warnings=warnings,
        )

    def resolve_node(self, node: ProvisionNode) -> ReferenceResolutionBatch:
        references = self.parser.parse_node(node)
        resolved_references = [self.resolve(reference) for reference in references]
        resolved_count = sum(
            1
            for item in resolved_references
            if item.status in {ReferenceResolutionStatus.RESOLVED_EXACT, ReferenceResolutionStatus.RESOLVED_MULTIPLE}
        )
        unresolved_count = sum(
            1
            for item in resolved_references
            if item.status in {ReferenceResolutionStatus.UNRESOLVED, ReferenceResolutionStatus.INVALID}
        )
        ambiguous_count = sum(1 for item in resolved_references if item.status == ReferenceResolutionStatus.AMBIGUOUS)
        warnings = [warning for item in resolved_references for warning in item.warnings]
        return ReferenceResolutionBatch(
            source_chunk_id=node.chunk_id,
            references=references,
            resolved_references=resolved_references,
            resolved_count=resolved_count,
            unresolved_count=unresolved_count,
            ambiguous_count=ambiguous_count,
            warnings=warnings,
        )

    def _target_law_id(self, reference: LegalReference, source_node: ProvisionNode | None) -> str | None:
        if reference.target_law_id:
            return reference.target_law_id
        if reference.reference_type in {LegalReferenceType.INTERNAL, LegalReferenceType.RELATIVE} and source_node is not None:
            return source_node.law_id
        return None


def _unresolved(reference: LegalReference, warnings: list[str]) -> ResolvedLegalReference:
    return ResolvedLegalReference(
        reference=reference,
        status=ReferenceResolutionStatus.UNRESOLVED,
        resolved_nodes=[],
        exact_node=None,
        warnings=warnings,
    )


def _node_location_warnings(reference: LegalReference, node: ProvisionNode) -> list[str]:
    warnings: list[str] = []
    for name, expected, actual in (
        ("target_law_id", reference.target_law_id, node.law_id),
        ("target_article_number", reference.target_article_number, node.article_number),
        ("target_clause_number", reference.target_clause_number, node.clause_number),
        ("target_point_number", reference.target_point_number, node.point_number),
    ):
        if expected is not None and actual is not None and expected != actual:
            warnings.append(f"{name} conflicts with resolved target_unit_id node.")
    return warnings
