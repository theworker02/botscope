"""Multi-sensor fan-in into a shared StreamingAggregator.

Status: IMPLEMENTED — local sensors only (log / pcap / iface), not Global federation.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from botscope.live.aggregator import ObservatorySnapshot, StreamingAggregator
from botscope.normalize.event import NormalizedEvent
from botscope.timeline.bucket import BucketResolution


class SensorKind(str, Enum):
    LOG = "log"
    PCAP = "pcap"
    IFACE = "iface"
    OTHER = "other"


@dataclass(frozen=True)
class SensorSource:
    """Descriptor for a local authorized sensor feed."""

    id: str
    kind: SensorKind
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "label": self.label or self.id,
        }


@dataclass
class FanInAggregator:
    """Merge events from multiple sensors into one rate-limited snapshot stream.

    Each event should carry ``sensor_id`` (stamped here if missing).
    """

    max_hz: float = 5.0
    resolution: BucketResolution = BucketResolution.MINUTE
    sources: dict[str, SensorSource] = field(default_factory=dict)
    _agg: StreamingAggregator = field(init=False, repr=False)
    _by_sensor: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        labels = [s.label or s.id for s in self.sources.values()]
        label = " + ".join(labels) if labels else "fan-in"
        self._agg = StreamingAggregator(
            max_hz=self.max_hz,
            resolution=self.resolution,
            source_label=label,
            is_demo=False,
        )

    def register(self, source: SensorSource) -> None:
        self.sources[source.id] = source
        labels = [s.label or s.id for s in self.sources.values()]
        self._agg.source_label = " + ".join(labels)

    def ingest(
        self,
        events: Iterable[NormalizedEvent],
        *,
        sensor_id: str | None = None,
    ) -> None:
        for event in events:
            self.ingest_one(event, sensor_id=sensor_id)

    def ingest_one(
        self,
        event: NormalizedEvent,
        *,
        sensor_id: str | None = None,
    ) -> None:
        sid = sensor_id or event.sensor_id or "unknown"
        if event.sensor_id != sid:
            event = event.model_copy(update={"sensor_id": sid})
        self._by_sensor[sid] = self._by_sensor.get(sid, 0) + 1
        self._agg.ingest_one(event)

    def maybe_snapshot(self, *, is_live: bool = True) -> ObservatorySnapshot | None:
        snap = self._agg.maybe_snapshot(is_live=is_live)
        return self._annotate(snap) if snap else None

    def snapshot(self, *, is_live: bool = True) -> ObservatorySnapshot:
        return self._annotate(self._agg.snapshot(is_live=is_live))

    def _annotate(self, snap: ObservatorySnapshot | None) -> ObservatorySnapshot | None:
        if snap is None:
            return None
        # Attach per-sensor counts via note (snapshot schema stays stable).
        parts = [f"{k}={v}" for k, v in sorted(self._by_sensor.items())]
        if parts:
            snap.note = (
                f"{snap.note} Sensors: {', '.join(parts)}."
            )
        return snap

    def sensor_counts(self) -> dict[str, int]:
        return dict(self._by_sensor)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sources": [s.to_dict() for s in self.sources.values()],
            "by_sensor": self.sensor_counts(),
            "source_label": self._agg.source_label,
        }
