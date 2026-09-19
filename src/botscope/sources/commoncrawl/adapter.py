"""Common Crawl adapter — zero-auth WEB CRAWL DATASET (not Internet traffic share)."""

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

COLLINFO_URL = "https://index.commoncrawl.org/collinfo.json"
PARSER_ID = "commoncrawl.collinfo.v1"


class CommonCrawlCatalogSource(DataSource):
    """Fetches Common Crawl collinfo.json — crawl catalog metadata only.

    Measurement perspective: WEB CRAWL DATASET.
    Never interpret crawl counts as Internet bot-traffic percentage.
    """

    source_id = "commoncrawl.collinfo"
    name = "Common Crawl Index Catalog"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.WEB_CRAWL_DATASET

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=600.0)
        self._last_receipt = None

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                COLLINFO_URL,
                source_id=self.source_id,
                parser=PARSER_ID,
                authentication="NONE",
                force=False,
                timeout=20.0,
            )
            self._last_receipt = receipt
            data = json.loads(body)
            if not isinstance(data, list) or not data:
                return AvailabilityReport(
                    source_id=self.source_id,
                    status=SourceStatus.DEGRADED,
                    detail="collinfo.json parsed but empty/unexpected",
                    http_status=receipt.http_status,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    authentication=self.authentication,
                    cached=receipt.from_cache,
                )
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.OFFLINE_CACHED if receipt.from_cache else SourceStatus.ACTIVE,
                detail=f"{len(data)} crawl indexes listed; latest={data[0].get('id')}",
                http_status=receipt.http_status,
                latency_ms=(time.perf_counter() - started) * 1000,
                authentication=self.authentication,
                cached=receipt.from_cache,
            )
        except Exception as exc:
            # Try stale cache body if present via force=False path failure
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.UNAVAILABLE,
                detail=f"availability check failed: {exc}",
                authentication=self.authentication,
            )

    def metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "authentication": self.authentication.value,
            "measurement_type": self.measurement_type.value,
            "perspective": "WEB CRAWL DATASET",
            "endpoint": COLLINFO_URL,
            "uses_for": [
                "crawl catalog / sampling frames",
                "longitudinal web crawl windows",
                "CDX endpoint discovery",
            ],
            "does_not_use_for": [
                "percentage of Internet traffic that is bots",
                "Cloudflare-equivalent HTTP botClass shares",
            ],
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        force = bool(query and query.extras.get("force"))
        body, receipt = self.cache.get(
            COLLINFO_URL,
            source_id=self.source_id,
            parser=PARSER_ID,
            authentication="NONE",
            force=force,
        )
        self._last_receipt = receipt
        data = json.loads(body)
        issues = self.validate(data)
        if issues:
            receipt.validation = "FAIL"
            receipt.validation_notes = issues
            raise ValueError(f"Common Crawl schema validation failed: {issues}")
        return {"collinfo": data, "receipt": receipt}

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "collinfo" in data:
            data = data["collinfo"]
        if not isinstance(data, list):
            return ["expected JSON list"]
        if not data:
            return ["empty crawl list"]
        first = data[0]
        required = ("id", "name", "cdx-api", "from", "to")
        missing = [k for k in required if k not in first]
        if missing:
            return [f"schema changed / missing keys on first entry: {missing}"]
        return []

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        if isinstance(response, dict) and "collinfo" in response:
            collinfo = response["collinfo"]
            receipt = response.get("receipt")
        else:
            collinfo = response
            receipt = self._last_receipt
        now = datetime.now(timezone.utc).isoformat()
        latest = collinfo[0]
        receipt_id = getattr(receipt, "receipt_id", None)
        limitations = [
            "Common Crawl is a WEB CRAWL DATASET, not a traffic share census.",
            "Do not derive Internet bot percentage from crawl catalogs.",
            "Coverage reflects crawler reach and politeness, not all networks.",
        ]
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.DIRECTLY_OBSERVED,
                metric_name="published_crawl_index_count",
                metric_value=len(collinfo),
                unit="indexes",
                population="Common Crawl published CDX index catalog",
                denominator="crawl indexes in collinfo.json",
                temporal_start=latest.get("from"),
                temporal_end=latest.get("to"),
                geographic_scope="Global web crawl sample",
                methodology_note=(
                    "Count of crawl collections advertised by index.commoncrawl.org/collinfo.json"
                ),
                limitations=limitations,
                extras={
                    "latest_crawl_id": latest.get("id"),
                    "latest_crawl_name": latest.get("name"),
                    "latest_cdx_api": latest.get("cdx-api"),
                    "perspective": "WEB CRAWL DATASET",
                },
                receipt_id=receipt_id,
            ),
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=str(uuid4()),
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.SOURCE_REPORTED,
                metric_name="latest_crawl_window",
                metric_value=f"{latest.get('from')} → {latest.get('to')}",
                unit=None,
                population=f"Crawl {latest.get('id')}",
                denominator="crawl wall-clock window",
                temporal_start=latest.get("from"),
                temporal_end=latest.get("to"),
                geographic_scope="Global web crawl sample",
                methodology_note="Window fields as published by Common Crawl",
                limitations=limitations,
                extras={"crawl_id": latest.get("id")},
                receipt_id=receipt_id,
            ),
        ]
