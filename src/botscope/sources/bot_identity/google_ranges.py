"""Google published crawler IP ranges — zero-auth identity evidence."""

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

COMMON_URL = (
    "https://developers.google.com/static/crawling/ipranges/common-crawlers.json"
)
SPECIAL_URL = (
    "https://developers.google.com/static/crawling/ipranges/special-crawlers.json"
)
PARSER_ID = "google.crawler_ip_ranges.v1"


class GoogleCrawlerRangesSource(DataSource):
    source_id = "google.crawler_ip_ranges"
    name = "Google Crawler IP Ranges"
    authentication = AuthenticationMode.NONE
    measurement_type = MeasurementType.BOT_IDENTITY_RANGES

    def __init__(self, cache: HttpSourceCache | None = None) -> None:
        self.cache = cache or HttpSourceCache(min_refresh_seconds=3600.0)
        self._last_receipt = None
        self._networks: list[ipaddress._BaseNetwork] = []
        self._networks_by_kind: dict[str, list[ipaddress._BaseNetwork]] = {
            "common": [],
            "special": [],
        }

    def availability(self) -> AvailabilityReport:
        started = time.perf_counter()
        try:
            body, receipt = self.cache.get(
                COMMON_URL,
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
                detail=f"{len(prefixes)} common prefixes; creationTime={data.get('creationTime')}",
                http_status=receipt.http_status,
                latency_ms=(time.perf_counter() - started) * 1000,
                authentication=self.authentication,
                cached=receipt.from_cache,
            )
        except Exception as exc:  # noqa: BLE001
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
            "urls": [COMMON_URL, SPECIAL_URL],
            "verification_note": (
                "IP range membership is evidence, not full verification. "
                "Prefer forward-confirmed reverse DNS per Google docs."
            ),
        }

    def _fetch_one(self, url: str, *, force: bool = False) -> dict[str, Any]:
        body, receipt = self.cache.get(
            url,
            source_id=self.source_id,
            parser=PARSER_ID,
            authentication="NONE",
            force=force,
        )
        data = json.loads(body)
        issues = validate_prefix_document(data)
        if issues:
            receipt.validation = "FAIL"
            receipt.validation_notes = issues
            raise ValueError(f"Google IP ranges schema validation failed: {issues}")
        return {"payload": data, "receipt": receipt, "url": url}

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        which = (query.extras.get("which") if query else None) or "both"
        force = bool(query and query.extras.get("force"))
        parts: dict[str, Any] = {}
        if which in {"common", "both"}:
            parts["common"] = self._fetch_one(COMMON_URL, force=force)
        if which in {"special", "both"}:
            try:
                parts["special"] = self._fetch_one(SPECIAL_URL, force=force)
            except Exception as exc:  # noqa: BLE001
                if which == "special":
                    raise
                parts["special_error"] = str(exc)
        # Prefer common receipt for health board linkage.
        primary = parts.get("common") or parts.get("special")
        self._last_receipt = primary["receipt"] if primary else None
        self._networks_by_kind = {
            "common": parse_prefix_list(parts["common"]["payload"]) if "common" in parts else [],
            "special": parse_prefix_list(parts["special"]["payload"]) if "special" in parts else [],
        }
        self._networks = list(self._networks_by_kind["common"]) + list(
            self._networks_by_kind["special"]
        )
        return parts

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "payload" in data:
            data = data["payload"]
        if isinstance(data, dict) and ("common" in data or "special" in data):
            issues: list[str] = []
            for key in ("common", "special"):
                if key in data and isinstance(data[key], dict):
                    issues.extend(validate_prefix_document(data[key].get("payload", data[key])))
            return issues
        return validate_prefix_document(data)

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        now = datetime.now(timezone.utc).isoformat()
        observations: list[NormalizedSourceObservation] = []
        if isinstance(response, dict) and ("common" in response or "special" in response):
            for kind in ("common", "special"):
                part = response.get(kind)
                if not isinstance(part, dict):
                    continue
                payload = part.get("payload") or {}
                receipt = part.get("receipt")
                prefixes = payload.get("prefixes") or []
                observations.append(
                    NormalizedSourceObservation(
                        source_id=self.source_id,
                        observation_id=str(uuid4()),
                        retrieved_at=now,
                        measurement_type=self.measurement_type,
                        kind=ObservationKind.SOURCE_REPORTED,
                        metric_name=f"published_prefix_count_{kind}",
                        metric_value=len(prefixes),
                        unit="cidrs",
                        population=f"Google-published {kind} crawler IP ranges",
                        denominator=f"CIDR prefixes in {kind}-crawlers.json",
                        temporal_start=payload.get("creationTime"),
                        temporal_end=payload.get("creationTime"),
                        geographic_scope="Global Google crawler egress",
                        methodology_note=f"Official Google {kind} crawler IP publication",
                        limitations=[
                            "Does not alone verify a User-Agent claim",
                            "IP match without DNS corroboration is incomplete verification",
                        ],
                        extras={
                            "creationTime": payload.get("creationTime"),
                            "which": kind,
                            "operator": "google",
                        },
                        receipt_id=getattr(receipt, "receipt_id", None),
                    )
                )
            return observations

        # Legacy single-payload shape
        payload = response["payload"] if isinstance(response, dict) and "payload" in response else response
        receipt = response.get("receipt") if isinstance(response, dict) else self._last_receipt
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
                population="Google-published crawler IP ranges",
                denominator="CIDR prefixes",
                temporal_start=payload.get("creationTime"),
                temporal_end=payload.get("creationTime"),
                geographic_scope="Global Google crawler egress",
                methodology_note="Official Google crawler IP publication",
                limitations=[
                    "Does not alone verify a User-Agent claim",
                    "Special-case crawlers use a separate file",
                ],
                extras={"creationTime": payload.get("creationTime"), "operator": "google"},
                receipt_id=getattr(receipt, "receipt_id", None),
            )
        ]

    def contains_ip(self, address: str) -> bool:
        if not self._networks:
            try:
                self.fetch()
            except Exception:  # noqa: BLE001
                return False
        return ip_in_networks(address, self._networks)
