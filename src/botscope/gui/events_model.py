"""Virtualized events table model for Observatory.

Status: IMPLEMENTED

Uses ``QAbstractTableModel`` + ``QTableView`` so millions of rows are not
materialized as ``QTableWidgetItem`` objects. Cell text is produced on demand
in ``data()``.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from botscope.normalize.event import NormalizedEvent

COLUMNS = (
    ("time", "Time"),
    ("category", "Category"),
    ("conf", "Conf"),
    ("method", "Method"),
    ("path", "Path"),
    ("user_agent", "User-Agent"),
)


class EventsTableModel(QAbstractTableModel):
    """Index-based model over a list of ``NormalizedEvent`` references."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._events: list[NormalizedEvent] = []

    def set_events(self, events: list[NormalizedEvent]) -> None:
        self.beginResetModel()
        self._events = events
        self.endResetModel()

    def events(self) -> list[NormalizedEvent]:
        return self._events

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(self._events)

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
        if parent is not None and parent.isValid():
            return 0
        return len(COLUMNS)

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(COLUMNS):
            return COLUMNS[section][1]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if not index.isValid() or not (0 <= index.row() < len(self._events)):
            return None
        event = self._events[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return event.event_id
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        col = index.column()
        if col == 0:
            return event.timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.timestamp else ""
        if col == 1:
            return event.classification or "UNKNOWN"
        if col == 2:
            return f"{event.confidence:.2f}" if event.confidence is not None else ""
        if col == 3:
            return event.http_method or ""
        if col == 4:
            return event.path or ""
        if col == 5:
            return event.user_agent or ""
        return None

    def event_at(self, row: int) -> NormalizedEvent | None:
        if 0 <= row < len(self._events):
            return self._events[row]
        return None

    def event_id_at(self, row: int) -> str | None:
        event = self.event_at(row)
        return event.event_id if event else None
