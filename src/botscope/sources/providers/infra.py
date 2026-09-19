"""Contextual infrastructure IP range sources (not bot traffic shares)."""

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


class CloudflareEdgeIpsSource(DataSource):
    """Cloudflare published edge IPv4 list — infrastructure context only."""

    source_id = "cloudflare.edge_ips"
    name = "Cloudflare Edge IPv4 Ranges"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.ROUTING

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=86400.0)
        self._last_receipt = None
        self.url = "https://www.cloudflare.com/ips-v4"

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                self.url,
                source_id=self.source_id,
                parser="cloudflare.edge_ips.v1",
                authentication="NONE",
                timeout=20.0,
            )
            self._last_receipt = receipt
            lines = [ln.strip() for ln in body.decode("utf-8", errors="replace").splitlines() if ln.strip()]
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.OFFLINE_CACHED if receipt.from_cache else SourceStatus.ACTIVE,
                detail=f"{len(lines)} IPv4 prefixes (infra context, not bot share)",
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
            parser="cloudflare.edge_ips.v1",
            authentication="NONE",
            force=bool(query and query.extras.get("force")),
        )
        self._last_receipt = receipt
        lines = [ln.strip() for ln in body.decode("utf-8", errors="replace").splitlines() if ln.strip()]
        return {"prefixes": lines, "receipt": receipt}

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "prefixes" in data:
            return [] if isinstance(data["prefixes"], list) else ["prefixes must be list"]
        return ["expected prefixes list"]

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        prefixes = response.get("prefixes") or []
        receipt = response.get("receipt")
        now = datetime.now(timezone.utc).isoformat()
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="published_edge_prefix_count",
                metric_value=len(prefixes),
                unit="cidrs",
                population="Cloudflare published edge IPv4 prefixes",
                denominator="Lines in ips-v4",
                methodology_note="Infrastructure context only — not Internet bot share",
                limitations=["Not a traffic classification source", "IPv4 list only"],
                extras={"tier": "C", "perspective": "INFRASTRUCTURE"},
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]


class AwsIpRangesSource(DataSource):
    """AWS public IP ranges JSON — cloud attribution context."""

    source_id = "aws.ip_ranges"
    name = "AWS Public IP Ranges"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.ROUTING

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=86400.0)
        self._last_receipt = None
        self.url = "https://ip-ranges.amazonaws.com/ip-ranges.json"

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                self.url,
                source_id=self.source_id,
                parser="aws.ip_ranges.v1",
                authentication="NONE",
                timeout=30.0,
            )
            self._last_receipt = receipt
            data = json.loads(body)
            prefixes = data.get("prefixes") or []
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.OFFLINE_CACHED if receipt.from_cache else SourceStatus.ACTIVE,
                detail=f"{len(prefixes)} IPv4 prefixes; syncToken={data.get('syncToken')}",
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
            "capabilities": ["ASN", "NETWORK_OWNER", "HISTORICAL_CONTEXT"],
            "note": "Cloud attribution — not bot traffic share",
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        body, receipt = self.cache.get(
            self.url,
            source_id=self.source_id,
            parser="aws.ip_ranges.v1",
            authentication="NONE",
            force=bool(query and query.extras.get("force")),
        )
        self._last_receipt = receipt
        data = json.loads(body)
        if "prefixes" not in data:
            raise ValueError("AWS ip-ranges schema missing prefixes")
        return {"payload": data, "receipt": receipt}

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "payload" in data:
            data = data["payload"]
        if not isinstance(data, dict) or "prefixes" not in data:
            return ["SOURCE SCHEMA CHANGED: missing prefixes"]
        return []

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"]
        receipt = response.get("receipt")
        prefixes = payload.get("prefixes") or []
        now = datetime.now(timezone.utc).isoformat()
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="published_prefix_count",
                metric_value=len(prefixes),
                unit="cidrs",
                population="AWS published IPv4 service prefixes",
                denominator="prefixes[] in ip-ranges.json",
                temporal_start=payload.get("createDate"),
                temporal_end=payload.get("createDate"),
                methodology_note="AWS public IP publication — cloud attribution context",
                limitations=["Not bot-specific", "Not an Internet traffic census"],
                extras={"tier": "C", "syncToken": payload.get("syncToken")},
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]
