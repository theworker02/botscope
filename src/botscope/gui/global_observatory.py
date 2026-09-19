"""Global Observatory panel — zero-config public sources (native Qt)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from botscope.estimation.internet import build_coverage_scorecard, estimate_from_federation
from botscope.gui.interactive import SourceConstellation, ZeroConfigBanner
from botscope.sources.cloudflare import CloudflareRadarSource
from botscope.sources.federation import zero_auth_federation
from botscope.ux import load_settings


class _CollectWorker(QThread):
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, federation, parent=None) -> None:
        super().__init__(parent)
        self._fed = federation

    def run(self) -> None:
        try:
            snap = self._fed.collect(probe_health=True)
            self.finished_ok.emit(snap)
        except Exception as exc:
            self.failed.emit(str(exc))


class GlobalObservatoryPanel(QWidget):
    """Multi-source real-data observatory — auto-loads zero-auth providers."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.federation = zero_auth_federation()
        self._last_snapshot = None
        self._auto_refreshed = False
        self._worker: _CollectWorker | None = None
        self._apply_optional_token()

        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Global Observatory")
        title.setObjectName("pageHeader")
        layout.addWidget(title)

        layout.addWidget(ZeroConfigBanner())

        self.mode_label = QLabel(
            "Auto-loading public crawler identity & infrastructure feeds… "
            "No API key required."
        )
        self.mode_label.setObjectName("muted")
        self.mode_label.setWordWrap(True)
        layout.addWidget(self.mode_label)

        gate = QLabel(
            "YOUR SERVER TRAFFIC: open a log/PCAP on Observatory — zero keys.\n"
            "PUBLIC REFERENCE FEEDS below auto-initialize (Google/Bing/OpenAI/… CIDRs, "
            "Common Crawl catalog, AWS/Cloudflare edge, GitHub meta).\n"
            "OPTIONAL BONUS: Cloudflare Radar (CDN traffic estimates) — only if YOU "
            "paste a free Radar Read token in Settings. Never required."
        )
        gate.setWordWrap(True)
        layout.addWidget(gate)

        self.constellation = SourceConstellation()
        self.constellation.source_clicked.connect(self._on_source_node)
        layout.addWidget(self.constellation, stretch=2)

        btns = QHBoxLayout()
        refresh = QPushButton("Refresh public sources")
        refresh.setObjectName("primaryButton")
        refresh.setToolTip("Re-fetch zero-auth providers (uses network; caches results)")
        refresh.clicked.connect(self.refresh_sources)
        btns.addWidget(refresh)
        self.radar_btn = QPushButton("About optional Radar…")
        self.radar_btn.setObjectName("ghostButton")
        self.radar_btn.clicked.connect(self._explain_radar)
        btns.addWidget(self.radar_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self.empty = QLabel("Fetching public sources automatically…")
        self.empty.setObjectName("muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty)

        split = QSplitter()
        split.setOrientation(Qt.Orientation.Vertical)
        self.health_view = QPlainTextEdit()
        self.health_view.setReadOnly(True)
        split.addWidget(self.health_view)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Source", "Measurement", "Value", "Population", "Kind"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_table_select)
        split.addWidget(self.table)
        self.explainer = QPlainTextEdit()
        self.explainer.setReadOnly(True)
        split.addWidget(self.explainer)
        layout.addWidget(split, stretch=2)
        self._split = split
        self._split.hide()

        note = QLabel(
            "Cached real observations are used offline. Demo data is never silently "
            "substituted for a failed public source."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self._seed_constellation()

    def _seed_constellation(self) -> None:
        nodes = []
        for sid, src in self.federation.sources.items():
            auth = src.authentication.value
            status = "AUTH_REQUIRED" if auth == "REQUIRED_TOKEN" else "AVAILABLE"
            if sid not in self.federation.enabled and auth == "REQUIRED_TOKEN":
                status = "AUTH_REQUIRED"
            nodes.append((sid, src.name, status))
        self.constellation.set_nodes(nodes)

    def ensure_loaded(self) -> None:
        if not self._auto_refreshed:
            self._auto_refreshed = True
            self.refresh_sources()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.ensure_loaded()

    def _apply_optional_token(self) -> None:
        settings = load_settings()
        token = (settings.cloudflare_radar_token or "").strip()
        if not token:
            # Keep Radar registered but disabled — never block the UI
            if "cloudflare.radar" in self.federation.enabled:
                self.federation.set_enabled("cloudflare.radar", False)
            return
        radar = self.federation.sources.get("cloudflare.radar")
        if isinstance(radar, CloudflareRadarSource):
            self.federation.sources["cloudflare.radar"] = CloudflareRadarSource(token=token)
            self.federation.set_enabled("cloudflare.radar", True)

    def _explain_radar(self) -> None:
        QMessageBox.information(
            self,
            "Optional Cloudflare Radar token",
            "You do NOT need this for YOUR server traffic.\n\n"
            "If you still want CDN-wide Radar estimates, create a MINIMAL token:\n\n"
            "1. dash.cloudflare.com → My Profile → API Tokens\n"
            "2. Create Token → Create Custom Token\n"
            "3. Permissions: Account → Radar → Read   (only that)\n"
            "4. Account Resources: Include → Specific account → your account\n"
            "5. Zone Resources: leave blank / unused\n"
            "6. Paste the token into Settings\n\n"
            "Do NOT grant DNS, Workers, Billing, or “all resources”.\n"
            "Docs: docs/sources/CLOUDFLARE_RADAR.md",
        )

    def _on_source_node(self, source_id: str) -> None:
        src = self.federation.sources.get(source_id)
        if src is None:
            return
        meta = {}
        try:
            meta = src.metadata() if hasattr(src, "metadata") else {}
        except Exception:
            meta = {}
        auth = src.authentication.value
        msg = [
            f"Source: {src.name}",
            f"ID: {source_id}",
            f"Authentication: {auth}",
            f"Enabled: {source_id in self.federation.enabled}",
        ]
        if auth == "REQUIRED_TOKEN":
            msg.append(
                "\nThis is OPTIONAL. BotScope works fully without it. "
                "Only unlocks CDN-wide Radar estimates."
            )
        else:
            msg.append("\nZERO-AUTH — no API key, no Connect button, no account.")
        if meta:
            msg.append(f"\nCapabilities: {meta.get('capabilities') or meta}")
        # Show health detail if we have a snapshot
        if self._last_snapshot and self._last_snapshot.health:
            for r in self._last_snapshot.health.reports:
                if r.source_id == source_id:
                    msg.append(f"\nState: {r.status.value}\n{r.detail}")
                    break
        QMessageBox.information(self, src.name, "\n".join(str(x) for x in msg))

    def _on_table_select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        item = self.table.item(rows[0].row(), 0)
        if item:
            # Map display name → source_id via federation
            name = item.text()
            for sid, src in self.federation.sources.items():
                if src.name == name or sid == name:
                    self._on_source_node(sid)
                    return

    def refresh_sources(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._apply_optional_token()
        self.mode_label.setText("Refreshing public sources in the background…")
        self.empty.setText("Fetching…")
        self.empty.show()
        self._worker = _CollectWorker(self.federation, self)
        self._worker.finished_ok.connect(self._on_collect_done)
        self._worker.failed.connect(self._on_collect_fail)
        self._worker.start()

    def _on_collect_fail(self, msg: str) -> None:
        self.mode_label.setText(f"Refresh failed: {msg}")
        self.empty.setText(
            "Could not refresh. Cached providers may still be AVAILABLE. "
            "Your local log analysis never depends on this."
        )

    def _on_collect_done(self, snapshot) -> None:
        self._last_snapshot = snapshot
        self.empty.hide()
        self._split.show()

        nodes = []
        if snapshot.health:
            by_id = {r.source_id: r for r in snapshot.health.reports}
            self.mode_label.setText(
                f"ZERO-AUTH ready · {snapshot.health.zero_auth_available}/"
                f"{snapshot.health.zero_auth_total} public sources available/cached · "
                f"Mode: {snapshot.health.mode}"
            )
            self.health_view.setPlainText(snapshot.health.format_text())
            for sid, src in self.federation.sources.items():
                report = by_id.get(sid)
                status = report.status.value if report else (
                    "AUTH_REQUIRED"
                    if src.authentication.value == "REQUIRED_TOKEN"
                    else "UNAVAILABLE"
                )
                nodes.append((sid, src.name, status))
        else:
            nodes = [(sid, src.name, "AVAILABLE") for sid, src in self.federation.sources.items()]
        self.constellation.set_nodes(nodes)

        rows = snapshot.raw_source_table()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            vals = [
                str(row.get("source")),
                str(row.get("measurement")),
                str(row.get("value")),
                str(row.get("population")),
                str(row.get("kind")),
            ]
            for col, text in enumerate(vals):
                self.table.setItem(i, col, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()

        estimate = estimate_from_federation(snapshot)
        coverage = build_coverage_scorecard(snapshot)
        lines = [
            "HOW WAS THIS CALCULATED?",
            f"Release gate: {estimate.release_gate}",
            f"Estimate: {estimate.estimate}",
            f"95% interval: {estimate.interval}",
            f"Population: {estimate.population}",
            f"Methodology: {estimate.methodology}",
            "",
            "API KEYS REQUIRED FOR THIS VIEW: none (zero-auth federation).",
            "Cloudflare Radar remains optional and disabled until you add a token.",
            "",
            "Coverage scorecard (not an accuracy score):",
            str(coverage),
            "",
            "Explainer:",
        ]
        for k, v in estimate.explainer.items():
            lines.append(f"  {k}: {v}")
        if snapshot.errors:
            lines += ["", "SOURCE FAILURES (not zeroed, not substituted):"]
            for sid, err in snapshot.errors.items():
                lines.append(f"  {sid}: {err}")
        self.explainer.setPlainText("\n".join(lines))
