"""Contextual public metadata feeds (Tier C — not bot-traffic shares)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from botscope.sources.base import (
    AuthenticationMode,
    AvailabilityReport,
    DataSource,
    MeasurementType,
    NormalizedSourceObservation,
    ObservationKind,
    SourceQuery,
    SourceStatus,
)
from botscope.sources.cache import HttpSourceCache


class GitHubMetaSource(DataSource):
    """GitHub /meta API — public hooks/pages/git IP hints for infra context."""

    source_id = "github.meta"
    name = "GitHub Meta IP Hints"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.ROUTING

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=86400.0)
        self._last_receipt = None
        self.url = "https://api.github.com/meta"

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                self.url,
                source_id=self.source_id,
                parser="github.meta.v1",
                authentication="NONE",
                timeout=20.0,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "BotScope/0.1",
                },
            )
            self._last_receipt = receipt
            data = json.loads(body)
            keys = [k for k in ("hooks", "web", "api", "git", "pages") if k in data]
            status = SourceStatus.CACHED if receipt.from_cache else SourceStatus.AVAILABLE
            return AvailabilityReport(
                source_id=self.source_id,
                status=status,
                detail=f"keys={keys} (infra context, not bot share)",
                http_status=receipt.http_status,
                latency_ms=(time.perf_counter() - started) * 1000,
                authentication=self.authentication,
                cached=receipt.from_cache,
            )
        except Exception as exc:
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.UNAVAILABLE,
                detail=str(exc),
                authentication=self.authentication,
            )

    def metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tier": "C",
            "capabilities": ["NETWORK_OWNER", "HISTORICAL_CONTEXT"],
            "note": "Not a bot-traffic percentage source",
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        body, receipt = self.cache.get(
            self.url,
            source_id=self.source_id,
            parser="github.meta.v1",
            authentication="NONE",
            force=bool(query and query.extras.get("force")),
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "BotScope/0.1",
            },
        )
        self._last_receipt = receipt
        return {"payload": json.loads(body), "receipt": receipt, "url": self.url}

    def validate(self, data: Any) -> list[str]:
        payload = data.get("payload") if isinstance(data, dict) else data
        if not isinstance(payload, dict):
            return ["expected object"]
        return []

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"] if isinstance(response, dict) else response
        receipt = response.get("receipt") if isinstance(response, dict) else self._last_receipt
        hooks = payload.get("hooks") if isinstance(payload, dict) else None
        n = len(hooks) if isinstance(hooks, list) else 0
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="github_hooks_prefix_count",
                metric_value=n,
                unit="cidrs",
                population="GitHub published service prefixes",
                denominator="Prefixes in api.github.com/meta",
                methodology_note=f"Public GitHub meta document: {self.url}",
                limitations=[
                    "Infrastructure context only — not bot/human traffic shares",
                    "Must not be presented as Internet-wide automation prevalence",
                ],
                extras={
                    "tier": "C",
                    "keys": list(payload)[:12] if isinstance(payload, dict) else [],
                },
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]


class GoogleCloudIpRangesSource(DataSource):
    """Google cloud / product IP ranges (goog.json) — infra context, not crawlers."""

    source_id = "google.cloud_ip_ranges"
    name = "Google Cloud / Product IP Ranges"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.ROUTING

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=86400.0)
        self._last_receipt = None
        self.url = "https://www.gstatic.com/ipranges/goog.json"

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                self.url,
                source_id=self.source_id,
                parser="google.cloud_ips.v1",
                authentication="NONE",
                timeout=20.0,
            )
            self._last_receipt = receipt
            data = json.loads(body)
            prefixes = data.get("prefixes") if isinstance(data, dict) else None
            n = len(prefixes) if isinstance(prefixes, list) else 0
            status = SourceStatus.CACHED if receipt.from_cache else SourceStatus.AVAILABLE
            return AvailabilityReport(
                source_id=self.source_id,
                status=status,
                detail=(
                    f"{n} prefixes; creationTime={data.get('creationTime')} "
                    "(Google product/cloud ranges — distinct from crawler feeds)"
                ),
                http_status=receipt.http_status,
                latency_ms=(time.perf_counter() - started) * 1000,
                authentication=self.authentication,
                cached=receipt.from_cache,
            )
        except Exception as exc:
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.UNAVAILABLE,
                detail=str(exc),
                authentication=self.authentication,
            )

    def metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tier": "B",
            "capabilities": ["IP_RANGE", "NETWORK_OWNER", "VALIDATION"],
            "note": "Not crawler identity — use google.crawler_ip_ranges for bots",
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        body, receipt = self.cache.get(
            self.url,
            source_id=self.source_id,
            parser="google.cloud_ips.v1",
            authentication="NONE",
            force=bool(query and query.extras.get("force")),
        )
        self._last_receipt = receipt
        return {"payload": json.loads(body), "receipt": receipt, "url": self.url}

    def validate(self, data: Any) -> list[str]:
        payload = data.get("payload") if isinstance(data, dict) else data
        if not isinstance(payload, dict) or "prefixes" not in payload:
            return ["expected goog.json with prefixes[]"]
        return []

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"] if isinstance(response, dict) else response
        receipt = response.get("receipt") if isinstance(response, dict) else self._last_receipt
        prefixes = payload.get("prefixes") if isinstance(payload, dict) else []
        n = len(prefixes) if isinstance(prefixes, list) else 0
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="google_cloud_prefix_count",
                metric_value=n,
                unit="cidrs",
                population="Google published cloud/product IP ranges (goog.json)",
                denominator="CIDR prefixes in goog.json",
                temporal_start=payload.get("creationTime") if isinstance(payload, dict) else None,
                methodology_note=f"Official Google feed: {self.url}",
                limitations=[
                    "These are Google product/cloud ranges, not crawler-only ranges",
                    "Do not confuse with google.crawler_ip_ranges",
                    "Not a bot-traffic percentage source",
                ],
                extras={"tier": "B", "creationTime": payload.get("creationTime")},
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]
