"""Microsoft Bingbot published IP ranges — zero-auth identity evidence."""

from __future__ import annotations

import ipaddress
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
from botscope.sources.bot_identity.cidr_util import (
    ip_in_networks,
    parse_prefix_list,
    validate_prefix_document,
)
from botscope.sources.cache import HttpSourceCache

BINGBOT_URL = "https://www.bing.com/toolbox/bingbot.json"
PARSER_ID = "bing.bingbot_ip_ranges.v1"


class BingbotRangesSource(DataSource):
    source_id = "bing.bingbot_ip_ranges"
    name = "Bingbot Published IP Ranges"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.BOT_IDENTITY_RANGES

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=3600.0)
        self._last_receipt = None
        self._networks: list[ipaddress._BaseNetwork] = []

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                BINGBOT_URL,
                source_id=self.source_id,
                parser=PARSER_ID,
                authentication="NONE",
                timeout=20.0,
            )
            self._last_receipt = receipt
            data = json.loads(body)
            prefixes = data.get("prefixes") or []
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.OFFLINE_CACHED if receipt.from_cache else SourceStatus.ACTIVE,
                detail=f"{len(prefixes)} prefixes; creationTime={data.get('creationTime')}",
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
            "name": self.name,
            "authentication": "NONE",
            "urls": [BINGBOT_URL],
            "verification_note": (
                "IP range membership is corroborating evidence for Bingbot claims. "
                "Prefer forward-confirmed reverse DNS under search.msn.com."
            ),
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        force = bool(query and query.extras.get("force"))
        body, receipt = self.cache.get(
            BINGBOT_URL,
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
            raise ValueError(f"Bingbot IP ranges schema validation failed: {issues}")
        self._networks = parse_prefix_list(data)
        return {"payload": data, "receipt": receipt, "url": BINGBOT_URL}

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "payload" in data:
            data = data["payload"]
        return validate_prefix_document(data)

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"] if isinstance(response, dict) and "payload" in response else response
        receipt = response.get("receipt") if isinstance(response, dict) else self._last_receipt
        now = datetime.now(timezone.utc).isoformat()
        prefixes = payload.get("prefixes") or []
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
                population="Microsoft-published Bingbot IP ranges",
                denominator="CIDR prefixes in bingbot.json",
                temporal_start=payload.get("creationTime"),
                temporal_end=payload.get("creationTime"),
                geographic_scope="Global Bingbot egress",
                methodology_note="Official Bingbot IP publication (toolbox/bingbot.json)",
                limitations=[
                    "Does not alone verify a User-Agent claim",
                    "Covers Bingbot published ranges only",
                ],
                extras={"creationTime": payload.get("creationTime"), "operator": "microsoft"},
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]

    def contains_ip(self, address: str) -> bool:
        if not self._networks:
            try:
                fetched = self.fetch()
                self._networks = parse_prefix_list(fetched["payload"])
            except Exception:
                return False
        return ip_in_networks(address, self._networks)
