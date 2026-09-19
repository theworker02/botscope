"""Cloudflare Radar adapter — OPTIONAL_AUTH_SOURCE (never ships tokens)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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

RADAR_BASE = "https://api.cloudflare.com/client/v4/radar"
# botClass summary endpoint documented by Cloudflare Radar HTTP APIs.
SUMMARY_BOT_CLASS = f"{RADAR_BASE}/http/summary/bot_class"


class CloudflareRadarSource(DataSource):
    """Cloudflare Radar HTTP botClass observations.

    Status: OPTIONAL_AUTH_SOURCE / AUTH_REQUIRED until user provides a token.
    BotScope never ships, scrapes, or bypasses tokens.
    """

    source_id = "cloudflare.radar"
    name = "Cloudflare Radar"
    authentication = AuthenticationMode.REQUIRED_TOKEN
    measurement_type = MeasurementType.PROVIDER_HTTP_TRAFFIC

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get(
            "BOTSCOPE_CLOUDFLARE_RADAR_TOKEN"
        )

    def availability(self) -> AvailabilityReport:
        if not self.token:
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.AUTH_REQUIRED,
                detail=(
                    "OPTIONAL_AUTH — Cloudflare Radar Read token not configured. "
                    "BotScope operates normally without this source. "
                    "Set a token in Settings to enable."
                ),
                authentication=self.authentication,
            )
        # Lightweight authenticated probe — do not invent endpoints.
        url = f"{SUMMARY_BOT_CLASS}?dateRange=7d&format=json"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "BotScope/0.1",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read()
                status = getattr(resp, "status", 200)
            data = json.loads(body)
            ok = bool(data.get("success", True))
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.ACTIVE if ok else SourceStatus.DEGRADED,
                detail="Authenticated Radar probe succeeded"
                if ok
                else f"Radar returned success={data.get('success')}",
                http_status=status,
                authentication=self.authentication,
            )
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                return AvailabilityReport(
                    source_id=self.source_id,
                    status=SourceStatus.AUTH_REQUIRED,
                    detail="Token rejected by Cloudflare API",
                    http_status=exc.code,
                    authentication=self.authentication,
                )
            return AvailabilityReport(
                source_id=self.source_id,
                status=SourceStatus.UNAVAILABLE,
                detail=f"HTTP {exc.code}",
                http_status=exc.code,
                authentication=self.authentication,
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
            "status": "OPTIONAL_AUTH_SOURCE",
            "authentication": "REQUIRED user-provided API token",
            "population": "HTTP traffic observed by Cloudflare's network",
            "never_claim": "percentage of all Internet traffic",
            "docs": "https://developers.cloudflare.com/radar/",
            "token_present": bool(self.token),
        }

    def fetch(self, query: SourceQuery | None = None) -> dict[str, Any]:
        if not self.token:
            raise PermissionError(
                "Cloudflare Radar requires a user-provided API token. "
                "Set CLOUDFLARE_API_TOKEN or pass token= to CloudflareRadarSource. "
                "BotScope will not bypass authentication."
            )
        date_range = (query.date_range if query and query.date_range else None) or "7d"
        url = f"{SUMMARY_BOT_CLASS}?dateRange={date_range}&format=json"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "BotScope/0.1",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            status = getattr(resp, "status", 200)
            content_type = resp.headers.get("Content-Type")
        data = json.loads(body)
        issues = self.validate(data)
        if issues:
            raise ValueError(
                "SOURCE SCHEMA CHANGED / validation failed for Cloudflare Radar: "
                + "; ".join(issues)
            )
        return {
            "payload": data,
            "http_status": status,
            "content_type": content_type,
            "url": url,
            "date_range": date_range,
        }

    def validate(self, data: Any) -> list[str]:
        if isinstance(data, dict) and "payload" in data:
            data = data["payload"]
        if not isinstance(data, dict):
            return ["expected JSON object"]
        # Cloudflare wraps results; accept several documented shapes but fail closed on trash.
        if "result" not in data and "summary_0" not in data:
            # Some responses nest under result.summary_0
            return ["SOURCE SCHEMA CHANGED: missing result/summary fields"]
        return []

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        payload = response["payload"] if "payload" in response else response
        date_range = response.get("date_range", "7d")
        now = datetime.now(timezone.utc).isoformat()
        result = payload.get("result") or payload
        summary = result.get("summary_0") or result.get("summary") or {}
        # Values may be strings like "43.123" — keep as SOURCE-REPORTED ratios when present.
        auto = _as_float(summary.get("bot") or summary.get("LIKELY_AUTOMATED"))
        human = _as_float(summary.get("human") or summary.get("LIKELY_HUMAN"))
        limitations = [
            "Population is Cloudflare-observed HTTP traffic only.",
            "Never display as 'percent of the Internet'.",
            "Classification uses Cloudflare botClass methodology.",
            "Cloudflare observes a large but non-random portion of activity.",
        ]
        obs: list[NormalizedSourceObservation] = []
        if auto is not None:
            # Cloudflare often returns percentages 0-100; normalize to fraction if >1.
            frac = auto / 100.0 if auto > 1.0 else auto
            obs.append(
                NormalizedSourceObservation(
                    source_id=self.source_id,
                    observation_id=str(uuid4()),
                    retrieved_at=now,
                    measurement_type=self.measurement_type,
                    kind=ObservationKind.SOURCE_REPORTED,
                    metric_name="likely_automated_share",
                    metric_value=frac,
                    unit="fraction",
                    population="Cloudflare-observed HTTP traffic (selected Radar dataset)",
                    denominator="HTTP requests (Cloudflare Radar botClass)",
                    geographic_scope="Cloudflare network coverage",
                    methodology_note=f"Radar HTTP summary bot_class dateRange={date_range}",
                    limitations=limitations,
                    extras={"raw_summary": summary, "date_range": date_range},
                )
            )
        if human is not None:
            frac = human / 100.0 if human > 1.0 else human
            obs.append(
                NormalizedSourceObservation(
                    source_id=self.source_id,
                    observation_id=str(uuid4()),
                    retrieved_at=now,
                    measurement_type=self.measurement_type,
                    kind=ObservationKind.SOURCE_REPORTED,
                    metric_name="likely_human_share",
                    metric_value=frac,
                    unit="fraction",
                    population="Cloudflare-observed HTTP traffic (selected Radar dataset)",
                    denominator="HTTP requests (Cloudflare Radar botClass)",
                    geographic_scope="Cloudflare network coverage",
                    methodology_note=f"Radar HTTP summary bot_class dateRange={date_range}",
                    limitations=limitations,
                    extras={"raw_summary": summary, "date_range": date_range},
                )
            )
        if not obs:
            obs.append(
                NormalizedSourceObservation(
                    source_id=self.source_id,
                    observation_id=str(uuid4()),
                    retrieved_at=now,
                    measurement_type=self.measurement_type,
                    kind=ObservationKind.SOURCE_REPORTED,
                    metric_name="radar_payload_received",
                    metric_value=1,
                    unit="flag",
                    population="Cloudflare Radar API response",
                    denominator="n/a",
                    methodology_note="Payload received but botClass fields not mapped",
                    limitations=[*limitations, "Adapter could not locate botClass summary fields"],
                    extras={"result_keys": list(result.keys())},
                )
            )
        return obs


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
