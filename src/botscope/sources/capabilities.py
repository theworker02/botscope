"""Source capability matrix and evidence sufficiency.

Status: IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from botscope.normalize.event import SourceType


@dataclass(frozen=True)
class SourceCapability:
    source_type: str
    observes: tuple[str, ...]
    typically_missing: tuple[str, ...]
    identity_strength: str  # weak | moderate | strong | none
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "observes": list(self.observes),
            "typically_missing": list(self.typically_missing),
            "identity_strength": self.identity_strength,
            "notes": self.notes,
        }


CAPABILITIES: dict[str, SourceCapability] = {
    SourceType.WEB_LOG.value: SourceCapability(
        SourceType.WEB_LOG.value,
        observes=("timestamp", "src_address", "http_method", "path", "status", "user_agent", "bytes_out"),
        typically_missing=("tls_metadata", "payload", "asn", "reverse_dns"),
        identity_strength="moderate",
        notes="Combined/common logs are the primary v0.1 ingest path.",
    ),
    SourceType.PROXY_LOG.value: SourceCapability(
        SourceType.PROXY_LOG.value,
        observes=("timestamp", "src_address", "host", "path", "user_agent", "status"),
        typically_missing=("payload", "tls_metadata"),
        identity_strength="moderate",
        notes="Proxy logs may include destination host more reliably than origin web logs.",
    ),
    SourceType.PCAP.value: SourceCapability(
        SourceType.PCAP.value,
        observes=("timestamp", "src_address", "dst_address", "src_port", "dst_port", "transport"),
        typically_missing=("user_agent", "path", "classification_context"),
        identity_strength="weak",
        notes="Classic PCAP via stdlib; PCAPNG via optional scapy. Metadata only.",
    ),
    SourceType.FLOW.value: SourceCapability(
        SourceType.FLOW.value,
        observes=("timestamp", "src_address", "dst_address", "bytes_in", "bytes_out", "duration"),
        typically_missing=("user_agent", "path", "http_method"),
        identity_strength="weak",
        notes="Flow records support volume analysis more than bot identity.",
    ),
    SourceType.APPLICATION.value: SourceCapability(
        SourceType.APPLICATION.value,
        observes=("timestamp", "path", "user_agent", "status"),
        typically_missing=("network_ports",),
        identity_strength="moderate",
        notes="Depends on application instrumentation richness.",
    ),
    SourceType.HONEYPOT.value: SourceCapability(
        SourceType.HONEYPOT.value,
        observes=("timestamp", "src_address", "path", "user_agent"),
        typically_missing=("human_baseline",),
        identity_strength="moderate",
        notes="Honeypot traffic is biased toward scanners/automation by design.",
    ),
    SourceType.HISTORICAL.value: SourceCapability(
        SourceType.HISTORICAL.value,
        observes=("timestamp", "varies"),
        typically_missing=("live_enrichment",),
        identity_strength="weak",
        notes="Historical corpora inherit original sensor limitations.",
    ),
    SourceType.DEMO.value: SourceCapability(
        SourceType.DEMO.value,
        observes=("synthetic_fields",),
        typically_missing=("real_world_validity",),
        identity_strength="none",
        notes="DEMO DATA — not real measurements. Never publish as observational results.",
    ),
    SourceType.UNKNOWN.value: SourceCapability(
        SourceType.UNKNOWN.value,
        observes=(),
        typically_missing=("almost_everything",),
        identity_strength="none",
        notes="Unknown source types should not be over-interpreted.",
    ),
}


@dataclass
class EvidenceSufficiency:
    source_type: str
    sufficient_for_volume: bool
    sufficient_for_shares: bool
    sufficient_for_identity: bool
    gaps: list[str] = field(default_factory=list)
    guidance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "sufficient_for_volume": self.sufficient_for_volume,
            "sufficient_for_shares": self.sufficient_for_shares,
            "sufficient_for_identity": self.sufficient_for_identity,
            "gaps": list(self.gaps),
            "guidance": self.guidance,
        }


def get_capability(source_type: str | SourceType) -> SourceCapability:
    key = source_type.value if isinstance(source_type, SourceType) else str(source_type)
    return CAPABILITIES.get(key, CAPABILITIES[SourceType.UNKNOWN.value])


def assess_evidence_sufficiency(
    source_type: str | SourceType,
    *,
    has_user_agent: bool = False,
    has_identity_signals: bool = False,
    event_count: int = 0,
) -> EvidenceSufficiency:
    cap = get_capability(source_type)
    gaps: list[str] = list(cap.typically_missing)
    volume_ok = event_count > 0 and cap.source_type != SourceType.UNKNOWN.value
    shares_ok = volume_ok and (has_user_agent or cap.identity_strength in {"moderate", "strong"})
    identity_ok = has_identity_signals and cap.identity_strength in {"moderate", "strong"}
    if cap.source_type == SourceType.DEMO.value:
        return EvidenceSufficiency(
            cap.source_type,
            sufficient_for_volume=True,
            sufficient_for_shares=False,
            sufficient_for_identity=False,
            gaps=["not_real_measurements"],
            guidance="Use demo only for UX walkthroughs; label all outputs as DEMO.",
        )
    guidance = "Suitable for local descriptive analysis." if shares_ok else "Increase field richness before claiming category shares."
    if not identity_ok:
        guidance += " Identity claims require stronger signals than UA alone."
    return EvidenceSufficiency(
        source_type=cap.source_type,
        sufficient_for_volume=volume_ok,
        sufficient_for_shares=shares_ok,
        sufficient_for_identity=identity_ok,
        gaps=gaps,
        guidance=guidance,
    )


def capability_matrix() -> list[dict[str, Any]]:
    return [c.to_dict() for c in CAPABILITIES.values()]
