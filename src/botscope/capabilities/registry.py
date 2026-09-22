"""Feature capability registry.

Status: IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FeatureStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    EXPERIMENTAL = "EXPERIMENTAL"
    PARTIAL = "PARTIAL"
    PLANNED = "PLANNED"
    RESEARCH = "RESEARCH"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True)
class FeatureCapability:
    id: str
    name: str
    status: FeatureStatus
    module: str
    owner: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "module": self.module,
            "owner": self.owner,
            "summary": self.summary,
        }


# Evidence-backed registry — update when code reality changes.
REGISTRY: list[FeatureCapability] = [
    FeatureCapability("analyze", "Offline analysis API", FeatureStatus.IMPLEMENTED, "botscope.api", "A1", "Analyzer pipeline"),
    FeatureCapability("classify", "Rule + identity classifier", FeatureStatus.IMPLEMENTED, "botscope.classify", "A1", "Evidence-backed heuristics"),
    FeatureCapability("ingest-weblog", "Combined/common log ingest", FeatureStatus.IMPLEMENTED, "botscope.ingest", "A1", "Primary parser"),
    FeatureCapability("storage-session", "Session store (.bscope)", FeatureStatus.IMPLEMENTED, "botscope.storage", "A1", "SQLite + JSONL"),
    FeatureCapability("reports", "JSON/MD/CSV/HTML reports", FeatureStatus.IMPLEMENTED, "botscope.reports", "A1", "Local exports"),
    FeatureCapability("privacy", "Privacy transforms", FeatureStatus.IMPLEMENTED, "botscope.privacy", "A1", "Redaction/hashing"),
    FeatureCapability("network", "Network contribution client", FeatureStatus.IMPLEMENTED, "botscope.network", "A1", "OFF by default"),
    FeatureCapability("signatures", "Bundled signature packs", FeatureStatus.IMPLEMENTED, "botscope.signatures", "A1", "Versioned JSON packs"),
    FeatureCapability(
        "gui",
        "Desktop Observatory GUI",
        FeatureStatus.IMPLEMENTED,
        "botscope.gui",
        "Shared",
        "Native Qt Observatory v2 workstation (not a web app)",
    ),
    FeatureCapability("cli", "Click CLI", FeatureStatus.IMPLEMENTED, "botscope.cli", "Shared", "Core + live/capture + research wrappers"),
    FeatureCapability("provenance", "Provenance inspector", FeatureStatus.IMPLEMENTED, "botscope.provenance", "A2", "Field + corpus audit"),
    FeatureCapability("quality", "Quality scorecard", FeatureStatus.IMPLEMENTED, "botscope.quality", "A2", "Multi-dimension"),
    FeatureCapability("compare", "Session compare", FeatureStatus.IMPLEMENTED, "botscope.compare", "A2", "Change detection"),
    FeatureCapability("compare-classifiers", "Classifier compare", FeatureStatus.IMPLEMENTED, "botscope.compare", "A2", "Agreement matrix"),
    FeatureCapability("research-export", "Research zip bundles", FeatureStatus.IMPLEMENTED, "botscope.research", "A2", "Citation + methodology"),
    FeatureCapability("query", "Safe event filter", FeatureStatus.IMPLEMENTED, "botscope.query", "A2", "GUI+CLI+Python"),
    FeatureCapability("annotations", "Researcher annotations", FeatureStatus.IMPLEMENTED, "botscope.annotations", "A2", "Separate from evidence"),
    FeatureCapability("workspace", "Analysis Workspace", FeatureStatus.IMPLEMENTED, "botscope.workspace", "Shared", "View-state in .bscope"),
    FeatureCapability("history", "Session history index", FeatureStatus.IMPLEMENTED, "botscope.history", "Shared", "Local MRU"),
    FeatureCapability("timeline", "Multi-resolution timeline", FeatureStatus.IMPLEMENTED, "botscope.timeline", "Shared", "GUI + streaming"),
    FeatureCapability("calibration", "Confidence calibration metrics", FeatureStatus.IMPLEMENTED, "botscope.calibration", "Shared", "Brier/ECE on labels"),
    FeatureCapability("eval", "Classification evaluation", FeatureStatus.IMPLEMENTED, "botscope.eval", "Shared", "P/R/F1 + confusion"),
    FeatureCapability("export-job", "Multi-format export job", FeatureStatus.IMPLEMENTED, "botscope.export", "Shared", "JSON/MD/HTML/CSV"),
    FeatureCapability("live-snapshots", "Streaming Observatory snapshots", FeatureStatus.IMPLEMENTED, "botscope.live", "Shared", "Bound Hz GUI refresh"),
    FeatureCapability("live-log-tail", "Authorized live log tail", FeatureStatus.IMPLEMENTED, "botscope.live", "Shared", "GUI Live tab + CLI"),
    FeatureCapability("live-persist", "Live SessionStore persistence", FeatureStatus.IMPLEMENTED, "botscope.live.persist", "Shared", "Append-only .bscope writer"),
    FeatureCapability("live-fanin", "Multi-sensor fan-in", FeatureStatus.IMPLEMENTED, "botscope.live.fanin", "Shared", "Local sensors → one aggregator"),
    FeatureCapability("live-alerts", "Snapshot threshold alerts", FeatureStatus.IMPLEMENTED, "botscope.live.alerts", "Shared", "Local measurement rules"),
    FeatureCapability("pcap-ingest", "PCAP/PCAPNG offline ingest", FeatureStatus.IMPLEMENTED, "botscope.ingest.pcap", "Shared", "Classic pcap stdlib; pcapng via scapy"),
    FeatureCapability("live-capture", "Live packet capture", FeatureStatus.IMPLEMENTED, "botscope.capture.live", "Shared", "Requires scapy + explicit auth"),
    FeatureCapability("geo", "Coarse geo aggregates", FeatureStatus.IMPLEMENTED, "botscope.geo", "Shared", "Offline table + IP≠person caveat"),
    FeatureCapability("asn", "Offline ASN table", FeatureStatus.IMPLEMENTED, "botscope.asn", "Shared", "Wired into Analyzer when BOTSCOPE_ASN_TABLE set"),
    FeatureCapability("diagnostics", "Doctor + bundle", FeatureStatus.IMPLEMENTED, "botscope.diagnostics", "A2", "Sanitized support zip"),
    FeatureCapability("plugin-sdk", "Plugin scaffold/validate", FeatureStatus.IMPLEMENTED, "botscope.plugins.sdk", "A2", "Templates"),
    FeatureCapability("botcard", "Bot Card library", FeatureStatus.IMPLEMENTED, "botscope.botcard", "A2", "Representation + index"),
    FeatureCapability("manifests", "Measurement manifests", FeatureStatus.IMPLEMENTED, "botscope.manifests", "A2", "Reproducibility metadata"),
    FeatureCapability("notebook", "Analysis notebook", FeatureStatus.EXPERIMENTAL, "botscope.notebook", "A2", "Lightweight cells + load/filter"),
    FeatureCapability("demo", "Bundled demo corpus", FeatureStatus.IMPLEMENTED, "botscope.demo", "A2", "Synthetic access log"),
    FeatureCapability(
        "onboarding-hello",
        "First-run hello command",
        FeatureStatus.IMPLEMENTED,
        "botscope.onboarding",
        "Shared",
        "Offline demo summary via botscope hello",
    ),
    FeatureCapability(
        "onboarding-access",
        "Ease-of-access checklist",
        FeatureStatus.IMPLEMENTED,
        "botscope.onboarding",
        "Shared",
        "botscope access + quickstart helpers",
    ),
    FeatureCapability("capture-helpers", "Capture plan/status", FeatureStatus.IMPLEMENTED, "botscope.capture", "A2", "No unauthorized probing"),
    FeatureCapability("enrich", "Local enrichment tags", FeatureStatus.IMPLEMENTED, "botscope.enrich", "A2", "ASN/geo composer + optional rDNS"),
    FeatureCapability("behavior", "Behavior profiles", FeatureStatus.IMPLEMENTED, "botscope.behavior", "A2", "Per-source features, entropy, bot-like score"),
    FeatureCapability("flows", "Flow aggregation", FeatureStatus.IMPLEMENTED, "botscope.flows", "A2", "From discrete events + majority class"),
    FeatureCapability("estimation", "Local + Internet estimates", FeatureStatus.IMPLEMENTED, "botscope.estimation", "A2", "Gated Internet headline via population_reliability_v1"),
    FeatureCapability("datasets", "Dataset helpers", FeatureStatus.IMPLEMENTED, "botscope.datasets", "A2", "Demo discovery"),
    FeatureCapability("ml-classifier", "ML classifier", FeatureStatus.IMPLEMENTED, "botscope.classify.ml", "A1", "Bundled feature_logistic_v1; never overrides verified identity"),
    FeatureCapability(
        "global-observatory",
        "Global Observatory federation",
        FeatureStatus.IMPLEMENTED,
        "botscope.sources",
        "Phase III",
        "Zero-auth Common Crawl + Google common/special + Bingbot; Radar OPTIONAL_AUTH",
    ),
    FeatureCapability(
        "identity-published-ranges",
        "Published crawler CIDR identity checks",
        FeatureStatus.IMPLEMENTED,
        "botscope.identity",
        "Phase III",
        "Google+Bing ranges loaded into Analyzer classify path (cache-first)",
    ),
    FeatureCapability(
        "internet-estimate-gate",
        "Internet estimate release gate",
        FeatureStatus.IMPLEMENTED,
        "botscope.estimation.internet",
        "Phase III",
        "INTERNET BOT TRAFFIC ESTIMATE opens with ≥2 weighted traffic shares + uncertainty",
    ),
]

def list_features(*, status: FeatureStatus | str | None = None) -> list[FeatureCapability]:
    if status is None:
        return list(REGISTRY)
    if isinstance(status, str):
        status = FeatureStatus(status)
    return [f for f in REGISTRY if f.status is status]


def get_feature(feature_id: str) -> FeatureCapability | None:
    for f in REGISTRY:
        if f.id == feature_id:
            return f
    return None


def features_matrix() -> list[dict[str, Any]]:
    return [f.to_dict() for f in REGISTRY]
