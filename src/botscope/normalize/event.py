"""Canonical normalized event model and measurement provenance."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceLevel(str, Enum):
    """Explicit measurement provenance — never conflate these levels."""

    OBSERVED = "OBSERVED"
    CLASSIFIED = "CLASSIFIED"
    INFERRED = "INFERRED"
    ESTIMATED = "ESTIMATED"


class SourceType(str, Enum):
    WEB_LOG = "web_log"
    PROXY_LOG = "proxy_log"
    PCAP = "pcap"
    FLOW = "flow"
    APPLICATION = "application"
    HONEYPOT = "honeypot"
    HISTORICAL = "historical"
    DEMO = "demo"
    UNKNOWN = "unknown"


class NormalizedEvent(BaseModel):
    """Canonical internal event representation.

    Missing fields remain unset. Do not fabricate values.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    sensor_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: SourceType = SourceType.UNKNOWN
    protocol: str | None = None
    src_address: str | None = None
    dst_address: str | None = None
    src_port: int | None = None
    dst_port: int | None = None
    transport: str | None = None
    http_method: str | None = None
    host: str | None = None
    path: str | None = None
    status: int | None = None
    user_agent: str | None = None
    bytes_in: int | None = None
    bytes_out: int | None = None
    duration: float | None = None
    asn: int | None = None
    network_owner: str | None = None
    reverse_dns: str | None = None
    forward_dns: str | None = None
    tls_metadata: dict[str, Any] | None = None
    classification: str | None = None
    confidence: float | None = None
    evidence: list[str] = Field(default_factory=list)
    privacy_transform: list[str] = Field(default_factory=list)
    provenance: ProvenanceLevel = ProvenanceLevel.OBSERVED
    raw_ref: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)

    def with_classification(
        self,
        category: str,
        confidence: float,
        evidence: list[str],
    ) -> NormalizedEvent:
        """Return a copy marked CLASSIFIED with evidence attached."""
        return self.model_copy(
            update={
                "classification": category,
                "confidence": confidence,
                "evidence": list(evidence),
                "provenance": ProvenanceLevel.CLASSIFIED,
            }
        )
