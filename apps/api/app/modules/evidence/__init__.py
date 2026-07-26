"""Evidence-domain utilities shared by downstream retrieval and generation stages."""

from app.modules.evidence.hierarchy_index import LegalProvisionHierarchyIndex
from app.modules.evidence.models import (
    HierarchyBuildReport,
    HierarchyWarning,
    LegalReference,
    LegalReferenceType,
    ProvisionLevel,
    ProvisionLocation,
    ProvisionLookupResult,
    ProvisionNode,
    ReferenceResolutionBatch,
    ReferenceResolutionStatus,
    ResolvedLegalReference,
)
from app.modules.evidence.reference_parser import LegalReferenceParser
from app.modules.evidence.reference_resolver import LegalReferenceResolver

__all__ = [
    "HierarchyBuildReport",
    "HierarchyWarning",
    "LegalProvisionHierarchyIndex",
    "LegalReference",
    "LegalReferenceParser",
    "LegalReferenceResolver",
    "LegalReferenceType",
    "ProvisionLevel",
    "ProvisionLocation",
    "ProvisionLookupResult",
    "ProvisionNode",
    "ReferenceResolutionBatch",
    "ReferenceResolutionStatus",
    "ResolvedLegalReference",
]
