"""Sources registry panel — live catalog + health, not static labels."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from botscope.sources.base import SourceStatus
from botscope.sources.registry import REGISTRY


def _display_status(raw: str) -> str:
    """Normalize legacy / synonym statuses for the UI."""
    mapping = {
        "OFFLINE_CACHED": SourceStatus.CACHED.value,
        "NOT_CONNECTED": SourceStatus.AUTH_REQUIRED.value,
        "ACTIVE": SourceStatus.AVAILABLE.value,  # health probe ≠ contributed evidence
    }
    return mapping.get(raw, raw)


class _ProbeWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        try:
            from botscope.sources.federation import zero_auth_federation

            fed = zero_auth_federation()
            board = fed.health()
            self.finished_ok.emit(board)
        except Exception as exc:
            self.failed.emit(str(exc))


class SourcesRegistryPanel(QWidget):
    """Structured view of registered sources and last known health."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Source Health")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "Public / zero-auth providers initialize automatically — no Connect button. "
            "States: AVAILABLE, CACHED, DEGRADED, STALE, RATE LIMITED, UNAVAILABLE, "
            "AUTH REQUIRED, DISABLED, ERROR. "
            "ACTIVE is reserved for sources that contributed evidence to the current analysis."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.summary = QLabel("Initializing source fabric…")
        self.summary.setObjectName("muted")
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Provider", "Auth", "Type", "State", "Detail / endpoints"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.table, stretch=2)

        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMaximumHeight(140)
        self.detail.setPlaceholderText("Select a provider for details…")
        layout.addWidget(self.detail)

        row = QHBoxLayout()
        refresh = QPushButton("Refresh health")
        refresh.setObjectName("primaryButton")
        refresh.setToolTip("Probes zero-auth endpoints in the background (may use network)")
        refresh.clicked.connect(self.probe_availability)
        row.addWidget(refresh)
        row.addStretch()
        layout.addLayout(row)

        self.health_note = QLabel("")
        self.health_note.setObjectName("muted")
        self.health_note.setWordWrap(True)
        layout.addWidget(self.health_note)

        self._probe: _ProbeWorker | None = None
        self._last_health: dict[str, object] = {}
        self.refresh()

    def refresh(self) -> None:
        """Fill registry rows without network I/O."""
        self.table.setRowCount(len(REGISTRY))
        for i, entry in enumerate(REGISTRY):
            endpoints = ", ".join(entry.endpoints[:2]) if entry.endpoints else "—"
            auth = "NONE" if not entry.authentication_required else "AUTH REQUIRED (optional)"
            status = _display_status(entry.status.value)
            if entry.source_id == "botscope.local_sensor":
                status = SourceStatus.AVAILABLE.value
            vals = [
                entry.name,
                auth,
                entry.measurement_type.value,
                status,
                endpoints,
            ]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, entry.source_id)
                self.table.setItem(i, col, item)
        self.table.resizeColumnsToContents()
        zero = sum(1 for e in REGISTRY if not e.authentication_required)
        self.summary.setText(
            f"{len(REGISTRY)} registered · {zero} zero-auth · "
            "no manual connection for public providers"
        )
        self.health_note.setText(
            "Click Refresh health for live reachability. "
            "Cached metadata is used when offline. Network contribution remains OFF by default."
        )

    def probe_availability(self) -> None:
        if self._probe and self._probe.isRunning():
            return
        self.health_note.setText("Probing sources…")
        self._probe = _ProbeWorker(self)
        self._probe.finished_ok.connect(self._on_probe_done)
        self._probe.failed.connect(self._on_probe_fail)
        self._probe.start()

    def _on_probe_fail(self, msg: str) -> None:
        self.health_note.setText(f"Probe failed: {msg}")

    def _on_probe_done(self, board) -> None:
        health = {h.source_id: h for h in board.reports}
        self._last_health = health
        counts: dict[str, int] = {}
        self.table.setRowCount(len(REGISTRY))
        for i, entry in enumerate(REGISTRY):
            report = health.get(entry.source_id)
            if report is not None:
                status = _display_status(report.status.value)
                detail = report.detail or ""
            else:
                status = _display_status(entry.status.value)
                detail = ", ".join(entry.endpoints[:2]) if entry.endpoints else "—"
            counts[status] = counts.get(status, 0) + 1
            auth = "NONE" if not entry.authentication_required else "AUTH REQUIRED (optional)"
            vals = [
                entry.name,
                auth,
                entry.measurement_type.value,
                status,
                detail[:120],
            ]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, entry.source_id)
                self.table.setItem(i, col, item)
        self.table.resizeColumnsToContents()
        parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
        self.summary.setText(" · ".join(parts) if parts else "No reports")
        self.health_note.setText(
            f"Zero-auth available/cached: {board.zero_auth_available}/"
            f"{board.zero_auth_total}. Mode: {board.mode}."
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_auto_probed", False):
            self._auto_probed = True
            self.probe_availability()

    def _on_select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        item = self.table.item(row, 0)
        if item is None:
            return
        source_id = item.data(Qt.ItemDataRole.UserRole)
        entry = next((e for e in REGISTRY if e.source_id == source_id), None)
        if entry is None:
            return
        report = self._last_health.get(source_id) if self._last_health else None
        lines = [
            f"Name: {entry.name}",
            f"ID: {entry.source_id}",
            f"Operator: {entry.operator}",
            f"Auth: {'NONE' if not entry.authentication_required else 'AUTH REQUIRED (optional)'}",
            f"Type: {entry.measurement_type.value}",
            f"Methodology: {entry.methodology}",
            f"Biases: {'; '.join(entry.known_biases)}",
            f"Notes: {entry.notes or '—'}",
            f"Homepage: {entry.homepage or '—'}",
        ]
        if report is not None:
            lines.insert(
                5,
                f"Live state: {_display_status(report.status.value)} — {report.detail}",
            )
            if report.status == SourceStatus.AUTH_REQUIRED or (
                hasattr(report.status, "value")
                and report.status.value == SourceStatus.AUTH_REQUIRED.value
            ):
                lines.append(
                    "This optional provider requires credentials. "
                    "BotScope operates normally without it."
                )
        self.detail.setPlainText("\n".join(lines))
