"""GUI-facing streaming snapshot bridge.

Re-exports live aggregator types and provides a Qt QObject that rate-limits
``snapshot_ready`` signals for Observatory panels.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from botscope.live import ObservatorySnapshot, StreamingAggregator
from botscope.normalize.event import NormalizedEvent

__all__ = [
    "ObservatorySnapshot",
    "SnapshotPublisher",
    "StreamingAggregator",
]


class SnapshotPublisher(QObject):
    """Publish ``ObservatorySnapshot`` objects at a bounded Hz to the GUI thread."""

    snapshot_ready = Signal(object)  # ObservatorySnapshot

    def __init__(
        self,
        aggregator: StreamingAggregator | None = None,
        *,
        max_hz: float = 5.0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.aggregator = aggregator or StreamingAggregator(max_hz=max_hz)

    def ingest(self, events: list[NormalizedEvent], *, force: bool = False) -> None:
        self.aggregator.ingest(events)
        snap = self.aggregator.snapshot(force_mark_emit=True) if force else self.aggregator.maybe_snapshot()
        if snap is not None:
            self.snapshot_ready.emit(snap)

    def ingest_one(self, event: NormalizedEvent, *, force: bool = False) -> None:
        self.ingest([event], force=force)

    def flush(self) -> ObservatorySnapshot:
        snap = self.aggregator.snapshot(force_mark_emit=True)
        self.snapshot_ready.emit(snap)
        return snap
