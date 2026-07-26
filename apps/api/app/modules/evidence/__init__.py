"""Evidence-domain utilities shared by downstream retrieval and generation stages."""

from app.modules.evidence.dependency_detector import LegalDependencyDetector
from app.modules.evidence.hierarchy_index import LegalProvisionHierarchyIndex
from app.modules.evidence.models import (
    DependencyReason,
    DependencySignal,
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
    "DependencyReason",
    "DependencySignal",
    "HierarchyBuildReport",
    "HierarchyWarning",
    "LegalDependencyDetector",
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

