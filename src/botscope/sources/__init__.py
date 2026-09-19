"""BotScope sources package — capability matrix + public data federation.

Status: IMPLEMENTED (federation foundation) / PARTIAL (optional Radar auth)
"""

from __future__ import annotations

from botscope.sources.base import (
    AuthenticationMode,
    AvailabilityReport,
    Cadence,
    DataSource,
    MeasurementType,
    NormalizedSourceObservation,
    ObservationKind,
    SourceQuery,
    SourceStatus,
)
from botscope.sources.capabilities import (
    CAPABILITIES,
    EvidenceSufficiency,
    SourceCapability,
    assess_evidence_sufficiency,
    capability_matrix,
    get_capability,
)
from botscope.sources.federation import (
    FederationSnapshot,
    SourceFederation,
    default_sources,
    zero_auth_federation,
)
from botscope.sources.health import SourceHealthBoard, probe_sources
from botscope.sources.registry import REGISTRY, get_entry, registry_as_dicts

__all__ = [
    "CAPABILITIES",
    "REGISTRY",
    "AuthenticationMode",
    "AvailabilityReport",
    "Cadence",
    "DataSource",
    "EvidenceSufficiency",
    "FederationSnapshot",
    "MeasurementType",
    "NormalizedSourceObservation",
    "ObservationKind",
    "SourceCapability",
    "SourceFederation",
    "SourceHealthBoard",
    "SourceQuery",
    "SourceStatus",
    "assess_evidence_sufficiency",
    "capability_matrix",
    "default_sources",
    "get_capability",
    "get_entry",
    "probe_sources",
    "registry_as_dicts",
    "zero_auth_federation",
]
