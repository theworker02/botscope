"""Local user-provided sensor adapter — emits traffic shares from session stats."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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


class LocalSensorSource(DataSource):
    source_id = "botscope.local_sensor"
    name = "Local BotScope Sensor"
    authentication = AuthenticationMode.USER_PROVIDED
    measurement_type = MeasurementType.LOCAL_SENSOR

    def availability(self) -> AvailabilityReport:
        return AvailabilityReport(
            source_id=self.source_id,
            status=SourceStatus.ACTIVE,
            detail="Emits automated_share when session stats are provided via SourceQuery.extras",
            authentication=self.authentication,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "note": "Fed by local Observatory sessions / analyze results",
        }

    def fetch(self, query: SourceQuery | None = None) -> Any:
        extras = (query.extras if query else {}) or {}
        return {
            "automated_share": extras.get("automated_share"),
            "event_count": extras.get("event_count"),
            "population": extras.get("population")
            or "Authorized local BotScope sensor / session",
            "temporal_start": extras.get("temporal_start"),
            "temporal_end": extras.get("temporal_end"),
            "weight": extras.get("weight"),
        }

    def normalize(self, response: Any) -> list[NormalizedSourceObservation]:
        if not isinstance(response, dict):
            return []
        share = response.get("automated_share")
        if share is None:
            return []
        try:
            value = float(share)
        except (TypeError, ValueError):
            return []
        now = datetime.now(timezone.utc).isoformat()
        extras: dict[str, Any] = {}
        if response.get("event_count") is not None:
            extras["event_count"] = response["event_count"]
        if response.get("weight") is not None:
            extras["weight"] = response["weight"]
        return [
            NormalizedSourceObservation(
                source_id=self.source_id,
                observation_id=f"{self.source_id}:automated_share",
                retrieved_at=now,
                measurement_type=self.measurement_type,
                kind=ObservationKind.BOTSCOPE_CLASSIFIED,
                metric_name="automated_share",
                metric_value=value,
                unit="fraction",
                population=str(response.get("population") or "Authorized local sensor"),
                denominator="http_requests",
                temporal_start=response.get("temporal_start"),
                temporal_end=response.get("temporal_end"),
                methodology_note=(
                    "CLASSIFIED automated share from authorized local BotScope analysis"
                ),
                limitations=[
                    "Local sensor selection bias",
                    "Not a global census alone",
                ],
                extras=extras,
            )
        ]
