"""Public Python API — Analyzer and analysis results."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from botscope.__version__ import __version__
from botscope.asn import AsnTable, load_asn_table
from botscope.behavior import profile_by_source
from botscope.classify.engine import Classifier
from botscope.classify.ml import MlModel
from botscope.classify.result import MODEL_VERSION, RULESET_VERSION
from botscope.enrich import enrich_event
from botscope.flows import aggregate_flows
from botscope.geo import aggregate_geo, load_geo_table
from botscope.geo.table import GeoTable
from botscope.identity import (
    IdentityEngine,
    PublishedRangeIndex,
    load_published_range_index,
)
from botscope.ingest.parsers import iter_events
from botscope.native import native_status
from botscope.normalize.event import NormalizedEvent
from botscope.privacy.transforms import PrivacyConfig, PrivacyTransform
from botscope.reports.generator import build_report
from botscope.signatures.store import SignatureStore
from botscope.statistics.aggregate import ObservatoryStats, aggregate_events
from botscope.storage.session import SessionStore


def _env_ranges_enabled() -> bool:
    flag = os.environ.get("BOTSCOPE_NO_IDENTITY_RANGES", "").strip().lower()
    return flag not in {"1", "true", "yes", "on"}


@dataclass
class AnalysisResult:
    events: list[NormalizedEvent]
    stats: ObservatoryStats
    session_path: Path | None = None
    session_id: str | None = None
    report: dict[str, Any] = field(default_factory=dict)
    is_demo: bool = False
    identity_ranges: dict[str, Any] = field(default_factory=dict)
    flows: list[dict[str, Any]] = field(default_factory=list)
    behavior: list[dict[str, Any]] = field(default_factory=list)
    geo: dict[str, Any] = field(default_factory=dict)

    @property
    def automation_fraction(self) -> float | None:
        return self.stats.automation_fraction("requests")

    @property
    def human_fraction(self) -> float | None:
        return self.stats.human_fraction("requests")

    @property
    def unknown_fraction(self) -> float | None:
        return self.stats.unknown_fraction("requests")


class Analyzer:
    """High-level analysis workflow used by CLI, GUI, and Python API."""

    def __init__(
        self,
        *,
        privacy: PrivacyConfig | None = None,
        classifier: Classifier | None = None,
        use_identity_ranges: bool | None = None,
        range_index: PublishedRangeIndex | None = None,
        asn_table: AsnTable | None = None,
        geo_table: GeoTable | None = None,
        ml_model: MlModel | None = None,
        enable_ml: bool | None = None,
        enable_rdns: bool | None = None,
    ) -> None:
        self.privacy = PrivacyTransform(privacy or PrivacyConfig())
        self.signatures = SignatureStore.load_bundled()
        self.identity_ranges_status: dict[str, Any] = {
            "enabled": False,
            "prefix_count": 0,
            "detail": "not loaded",
        }
        if enable_rdns is None:
            enable_rdns = os.environ.get("BOTSCOPE_RDNS", "").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self.enable_rdns = bool(enable_rdns)

        if use_identity_ranges is None:
            use_identity_ranges = _env_ranges_enabled()

        if enable_ml is None:
            # Default ON; opt out with BOTSCOPE_ML=0/false/off
            flag = os.environ.get("BOTSCOPE_ML", "1").strip().lower()
            enable_ml = flag not in {"0", "false", "no", "off"}
        resolved_ml = ml_model
        if resolved_ml is None and enable_ml:
            ml_path = os.environ.get("BOTSCOPE_ML_MODEL")
            resolved_ml = MlModel.load(ml_path)

        if classifier is not None:
            self.classifier = classifier
        else:
            index = range_index
            if index is None and use_identity_ranges:
                index, self.identity_ranges_status = load_published_range_index(enabled=True)
            elif index is not None:
                self.identity_ranges_status = {
                    "enabled": True,
                    "prefix_count": len(index),
                    "operators": sorted(index.networks_by_operator.keys()),
                    "detail": f"Injected index with {len(index)} prefixes",
                    "errors": {},
                    "sources": {},
                }
            else:
                index = PublishedRangeIndex()
                self.identity_ranges_status = {
                    "enabled": False,
                    "prefix_count": 0,
                    "detail": "Identity published ranges disabled",
                    "errors": {},
                    "sources": {},
                }
            identity = IdentityEngine(self.signatures, range_index=index)
            self.classifier = Classifier(
                signatures=self.signatures,
                identity=identity,
                ml_model=resolved_ml,
            )

        if asn_table is not None:
            self.asn_table = asn_table
        else:
            asn_path = os.environ.get("BOTSCOPE_ASN_TABLE")
            self.asn_table = load_asn_table(asn_path) if asn_path else AsnTable()

        if geo_table is not None:
            self.geo_table = geo_table
        else:
            geo_path = os.environ.get("BOTSCOPE_GEO_TABLE")
            self.geo_table = load_geo_table(geo_path) if geo_path else GeoTable()

    def analyze(
        self,
        source: str | Path | Iterable[NormalizedEvent],
        *,
        output: str | Path | None = None,
        is_demo: bool = False,
        max_events: int | None = None,
    ) -> AnalysisResult:
        if isinstance(source, (str, Path)):
            source_path = Path(source)
            source_hash = _file_hash(source_path)
            raw_events = iter_events(source_path)
        else:
            source_path = None
            source_hash = None
            raw_events = source

        classified: list[NormalizedEvent] = []
        for idx, event in enumerate(raw_events):
            if max_events is not None and idx >= max_events:
                break
            event = self._enrich_local(event)
            event = self.privacy.apply(event)
            result = self.classifier.classify(event)
            classified.append(
                event.with_classification(
                    category=result.category.value,
                    confidence=result.confidence,
                    evidence=[
                        ("+ " if e.polarity == "for" else "- ") + e.statement
                        for e in result.evidence
                    ],
                ).model_copy(
                    update={
                        "extras": {
                            **event.extras,
                            "attribution": result.attribution,
                            "identity_status": result.identity_status,
                            "matched_rules": result.extras.get("matched_rules", []),
                            "model_version": result.model_version,
                            "ruleset_version": result.ruleset_version,
                            "confidence_note": result.extras.get("confidence_note"),
                        }
                    }
                )
            )

        stats = aggregate_events(classified, is_demo=is_demo)
        flows = [f.to_dict() for f in aggregate_flows(classified)]
        behavior = [b.to_dict() for b in profile_by_source(classified)]
        geo = aggregate_geo(classified).to_dict()
        report = build_report(
            stats,
            events=classified,
            is_demo=is_demo,
            flows=flows,
            behavior=behavior,
            geo=geo,
        )
        if self.identity_ranges_status:
            report["identity_ranges"] = dict(self.identity_ranges_status)

        session_path = None
        session_id = None
        if output is not None:
            store = SessionStore(output)
            backend = native_status()
            session_id = store.create_session(
                source_path=str(source_path) if source_path else None,
                source_hash=source_hash,
                classifier_version=MODEL_VERSION,
                ruleset_version=RULESET_VERSION,
                signature_version=self.signatures.VERSION,
                native_backend=backend.get("backend"),
                is_demo=is_demo,
                config={
                    "botscope_version": __version__,
                    "identity_ranges": dict(self.identity_ranges_status),
                },
            )
            store.append_events(classified)
            for key, value in stats.to_dict().items():
                store.set_aggregate(session_id, key, value, stats.provenance.value)
            store.write_report(report)
            session_path = store.root
            store.close()

        return AnalysisResult(
            events=classified,
            stats=stats,
            session_path=session_path,
            session_id=session_id,
            report=report,
            is_demo=is_demo,
            identity_ranges=dict(self.identity_ranges_status),
            flows=flows,
            behavior=behavior,
            geo=geo,
        )

    def classify_event(self, event: NormalizedEvent):
        event = self._enrich_local(event)
        return self.classifier.classify(event)

    def _enrich_local(self, event: NormalizedEvent) -> NormalizedEvent:
        """Compose offline ASN/geo enrichment; optional rDNS when enabled."""
        return enrich_event(
            event,
            asn_table=self.asn_table,
            geo_table=self.geo_table,
            rdns=self.enable_rdns,
        )


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
