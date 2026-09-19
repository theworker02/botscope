"""Federation orchestrator — multi-source observations without fake averages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from botscope.sources.base import (
    DataSource,
    NormalizedSourceObservation,
    SourceQuery,
)
from botscope.sources.bot_identity import BingbotRangesSource, GoogleCrawlerRangesSource
from botscope.sources.cloudflare import CloudflareRadarSource
from botscope.sources.commoncrawl import CommonCrawlCatalogSource
from botscope.sources.health import SourceHealthBoard, probe_sources
from botscope.sources.providers import (
    AwsIpRangesSource,
    CloudflareEdgeIpsSource,
    GitHubMetaSource,
    GoogleCloudIpRangesSource,
    builtin_published_cidr_sources,
)


@dataclass
class FederationSnapshot:
    """Raw source-level measurements prior to any Internet estimate."""

    retrieved_at: str
    enabled_sources: list[str]
    observations: list[NormalizedSourceObservation] = field(default_factory=list)
    health: SourceHealthBoard | None = None
    errors: dict[str, str] = field(default_factory=dict)
    headline_gate: str = "MULTI-SOURCE BOT TRAFFIC OBSERVATIONS"
    note: str = (
        "Source percentages are not directly comparable across different populations. "
        "Internet-wide headline estimates remain gated until methodology criteria pass."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "retrieved_at": self.retrieved_at,
            "enabled_sources": list(self.enabled_sources),
            "observations": [o.to_dict() for o in self.observations],
            "health": self.health.to_dict() if self.health else None,
            "errors": dict(self.errors),
            "headline_gate": self.headline_gate,
            "note": self.note,
        }

    def raw_source_table(self) -> list[dict[str, Any]]:
        rows = []
        for o in self.observations:
            rows.append(
                {
                    "source": o.source_id,
                    "measurement": o.metric_name,
                    "value": o.metric_value,
                    "population": o.population,
                    "denominator": o.denominator,
                    "kind": o.kind.value,
                }
            )
        return rows


class SourceFederation:
    """Enable/disable sources and collect normalized observations."""

    def __init__(self, sources: list[DataSource] | None = None) -> None:
        self.sources: dict[str, DataSource] = {}
        self.enabled: set[str] = set()
        for src in sources or default_sources():
            self.register(src, enabled=src.authentication.value == "NONE")

    def register(self, source: DataSource, *, enabled: bool = True) -> None:
        self.sources[source.source_id] = source
        if enabled:
            self.enabled.add(source.source_id)
        else:
            self.enabled.discard(source.source_id)

    def set_enabled(self, source_id: str, enabled: bool) -> None:
        if source_id not in self.sources:
            raise KeyError(source_id)
        if enabled:
            self.enabled.add(source_id)
        else:
            self.enabled.discard(source_id)

    def health(self) -> SourceHealthBoard:
        return probe_sources(self.sources.values())

    def collect(
        self,
        *,
        probe_health: bool = True,
        queries: dict[str, SourceQuery] | None = None,
    ) -> FederationSnapshot:
        queries = queries or {}
        observations: list[NormalizedSourceObservation] = []
        errors: dict[str, str] = {}
        for source_id in sorted(self.enabled):
            src = self.sources[source_id]
            try:
                raw = src.fetch(queries.get(source_id))
                observations.extend(src.normalize(raw))
            except PermissionError as exc:
                errors[source_id] = str(exc)
            except Exception as exc:
                errors[source_id] = f"SOURCE UNAVAILABLE: {exc}"
        health = self.health() if probe_health else None
        return FederationSnapshot(
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            enabled_sources=sorted(self.enabled),
            observations=observations,
            health=health,
            errors=errors,
        )


def default_sources() -> list[DataSource]:
    sources: list[DataSource] = [
        CommonCrawlCatalogSource(),
        GoogleCrawlerRangesSource(),
        BingbotRangesSource(),
        *builtin_published_cidr_sources(),
        GoogleCloudIpRangesSource(),
        CloudflareEdgeIpsSource(),
        AwsIpRangesSource(),
        GitHubMetaSource(),
        CloudflareRadarSource(),  # registered but NOT enabled by default
    ]
    return sources


def zero_auth_federation() -> SourceFederation:
    fed = SourceFederation(default_sources())
    # Ensure Cloudflare Radar stays disabled until token + explicit enable
    if "cloudflare.radar" in fed.sources:
        fed.set_enabled("cloudflare.radar", False)
    return fed
