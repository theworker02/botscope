"""Additive Observatory workstation panels (Compare, Annotations, Export, History, Live).

These panels extend the existing PySide6 shell — they do not replace ObservatoryPanel.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from botscope.annotations import AnnotationStore
from botscope.compare import compare_classifiers, compare_sessions
from botscope.export import export_analysis
from botscope.gui.session_state import GuiSession
from botscope.history import SessionHistory
from botscope.workspace import AnalysisWorkspace


class ComparePanel(QWidget):
    """Session-to-session and dual time-window comparison (no causality claims)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Compare")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "Compare two saved sessions OR two time windows on the loaded dataset. "
            "Percentage-point (pp) change ≠ relative percent change."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.mode = QComboBox()
        self.mode.addItems(["Two .bscope sessions", "Two time windows (loaded dataset)"])
        layout.addWidget(self.mode)

        form = QFormLayout()
        self.left_path = QLineEdit()
        self.right_path = QLineEdit()
        browse_l = QPushButton("Browse…")
        browse_r = QPushButton("Browse…")
        browse_l.clicked.connect(lambda: self._browse(self.left_path))
        browse_r.clicked.connect(lambda: self._browse(self.right_path))
        row_l = QHBoxLayout()
        row_l.addWidget(self.left_path)
        row_l.addWidget(browse_l)
        row_r = QHBoxLayout()
        row_r.addWidget(self.right_path)
        row_r.addWidget(browse_r)
        left_wrap = QWidget()
        left_wrap.setLayout(row_l)
        right_wrap = QWidget()
        right_wrap.setLayout(row_r)
        form.addRow("Left .bscope:", left_wrap)
        form.addRow("Right .bscope:", right_wrap)

        self.den = QComboBox()
        self.den.addItems(["requests", "bytes"])
        form.addRow("Denominator:", self.den)
        self.split = QComboBox()
        self.split.addItems(["First half vs second half", "Equal thirds: early vs late"])
        form.addRow("Window mode:", self.split)
        layout.addLayout(form)

        run = QPushButton("Run compare")
        run.setObjectName("primaryButton")
        run.clicked.connect(self._run_compare)
        layout.addWidget(run)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Metric", "A", "B", "Δ"])
        layout.addWidget(self.table, stretch=2)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details, stretch=1)
        self._session: GuiSession | None = None

    def refresh(self, session: GuiSession) -> None:
        self._session = session

    def _browse(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open .bscope", "", "BotScope sessions (*.bscope);;All (*.*)"
        )
        if path:
            target.setText(path)

    def _run_compare(self) -> None:
        if self.mode.currentIndex() == 1:
            self._run_window_compare()
            return
        left = self.left_path.text().strip()
        right = self.right_path.text().strip()
        if not left or not right:
            QMessageBox.information(self, "Compare", "Select two .bscope paths.")
            return
        try:
            report = compare_sessions(left, right)
        except Exception as exc:
            QMessageBox.critical(self, "Compare failed", str(exc))
            return
        self.table.setHorizontalHeaderLabels(["Category", "Left", "Right", "Δ"])
        deltas = getattr(report, "category_deltas", None) or []
        self.table.setRowCount(len(deltas))
        for i, delta in enumerate(deltas):
            self.table.setItem(i, 0, QTableWidgetItem(delta.category))
            self.table.setItem(i, 1, QTableWidgetItem(str(delta.left)))
            self.table.setItem(i, 2, QTableWidgetItem(str(delta.right)))
            self.table.setItem(i, 3, QTableWidgetItem(str(delta.delta)))
        self.table.resizeColumnsToContents()
        lines = [
            f"Left:  {report.left_label}  ({report.left_events:,} events)",
            f"Right: {report.right_label}  ({report.right_events:,} events)",
            f"Shared event IDs: {report.shared_event_ids:,}",
            f"Only left / only right: {report.only_left_ids:,} / {report.only_right_ids:,}",
            f"Classification changes: {len(report.classification_changes):,}",
            "",
            "No causality is inferred from these deltas.",
        ]
        for change in report.classification_changes[:25]:
            lines.append(
                f"  {change['event_id']}: {change['left_classification']} → "
                f"{change['right_classification']}"
            )
        self.details.setPlainText("\n".join(lines))

    def _run_window_compare(self) -> None:
        if self._session is None or not self._session.loaded:
            QMessageBox.information(self, "Compare", "Load a dataset first.")
            return
        from botscope.gui.anomaly import compare_windows

        events = list(self._session.events)
        timed = sorted(
            [e for e in events if e.timestamp is not None],
            key=lambda e: e.timestamp,  # type: ignore[arg-type, return-value]
        )
        if len(timed) < 4:
            QMessageBox.information(self, "Compare", "Need more timestamped events.")
            return
        if self.split.currentIndex() == 0:
            mid = len(timed) // 2
            a, b = timed[:mid], timed[mid:]
        else:
            third = max(1, len(timed) // 3)
            a, b = timed[:third], timed[-third:]
        result = compare_windows(
            events,
            start_a=a[0].timestamp,
            end_a=a[-1].timestamp,
            start_b=b[0].timestamp,
            end_b=b[-1].timestamp,
            denominator=self.den.currentText(),
        )
        self.table.setHorizontalHeaderLabels(["Metric", "A", "B", "Δ pp"])
        rows = result["rows"]
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            vals = [
                row["metric"],
                f"{row['window_a_share'] * 100:.1f}%",
                f"{row['window_b_share'] * 100:.1f}%",
                f"{row['percentage_point_change']:+.1f} pp",
            ]
            for c, text in enumerate(vals):
                self.table.setItem(i, c, QTableWidgetItem(text))
        lines = [result["note"], ""]
        for row in rows:
            lines.append(row["display"])
        lines.append(
            f"Window A events: {result['window_a_events']:,}  ·  "
            f"Window B events: {result['window_b_events']:,}"
        )
        self.details.setPlainText("\n".join(lines))


class ClassifierComparePanel(QWidget):
    """Re-run classifier vs stored labels for the loaded session."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Classifier Version Compare")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        layout.addWidget(self.body)
        btn = QPushButton("Compare live classifier vs stored labels")
        btn.clicked.connect(self._run)
        layout.addWidget(btn)
        self._session: GuiSession | None = None

    def refresh(self, session: GuiSession) -> None:
        self._session = session
        if not session.events:
            self.body.setPlainText("Load a session to compare classifier labels.")
        else:
            self.body.setPlainText(
                f"{len(session.events):,} events loaded. Run comparison to measure agreement."
            )

    def _run(self) -> None:
        if self._session is None or not self._session.events:
            QMessageBox.information(self, "Classifier compare", "No events loaded.")
            return
        report = compare_classifiers(self._session.events)
        data = report.to_dict()
        lines = [
            f"Left model: {data['left_model']}",
            f"Right model: {data['right_model']}",
            f"Events: {data['event_count']:,}",
            f"Agreement rate: {data['agreement_rate']:.4f}",
            "",
            data.get("note", ""),
            "",
            "Disagreements (sample):",
        ]
        for row in data.get("disagreements") or []:
            lines.append(f"  {row.get('event_id')}: {row.get('left')} vs {row.get('right')}")
        self.body.setPlainText("\n".join(lines))


class AnnotationsPanel(QWidget):
    """Researcher annotations — not classifier evidence."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Annotations")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        caveat = QLabel(
            "Annotations are researcher commentary. They are never treated as "
            "classifier evidence."
        )
        caveat.setObjectName("muted")
        caveat.setWordWrap(True)
        layout.addWidget(caveat)
        self.list = QListWidget()
        layout.addWidget(self.list, stretch=2)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Write an annotation…")
        layout.addWidget(self.editor)
        btn = QPushButton("Add annotation to current session")
        btn.clicked.connect(self._add)
        layout.addWidget(btn)
        self._session: GuiSession | None = None
        self._session_dir: Path | None = None

    def refresh(self, session: GuiSession) -> None:
        self._session = session
        self._session_dir = session.session_path
        self.list.clear()
        if session.session_path and Path(session.session_path).exists():
            store = AnnotationStore(session.session_path)
            try:
                for ann in store.list_annotations():
                    label = f"[{ann.created_at}] {ann.body[:120]}"
                    self.list.addItem(QListWidgetItem(label))
            finally:
                store.close()
        else:
            self.list.addItem(
                QListWidgetItem("Save the analysis as a .bscope session to persist annotations.")
            )

    def _add(self) -> None:
        if self._session is None:
            return
        body = self.editor.toPlainText().strip()
        if not body:
            return
        if not self._session.session_path:
            QMessageBox.information(
                self,
                "Annotations",
                "Save the analysis to a .bscope session first (File → Save Session).",
            )
            return
        store = AnnotationStore(self._session.session_path)
        try:
            sid = self._session.session_id or "default"
            store.add(
                sid,
                body,
                event_id=self._session.selected_event_id,
                author="observatory",
            )
        finally:
            store.close()
        self.editor.clear()
        self.refresh(self._session)


class ExportPanel(QWidget):
    """Report builder using botscope.export / reports."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Export / Report Builder")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        self.fmt_json = QCheckBox("JSON")
        self.fmt_md = QCheckBox("Markdown")
        self.fmt_html = QCheckBox("HTML")
        self.fmt_csv = QCheckBox("CSV categories")
        self.fmt_snapshot = QCheckBox("Observatory snapshot (JSON + Markdown)")
        self.fmt_json.setChecked(True)
        self.fmt_md.setChecked(True)
        self.fmt_snapshot.setChecked(True)
        for box in (
            self.fmt_json,
            self.fmt_md,
            self.fmt_html,
            self.fmt_csv,
            self.fmt_snapshot,
        ):
            layout.addWidget(box)
        btn = QPushButton("Export report…")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._export)
        layout.addWidget(btn)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        self._session: GuiSession | None = None

    def refresh(self, session: GuiSession) -> None:
        self._session = session
        if session.loaded:
            self.log.setPlainText(f"Ready to export {len(session.events):,} events.")
        else:
            self.log.setPlainText("Load an analysis first.")

    def _export(self) -> None:
        if self._session is None or self._session.result is None:
            QMessageBox.information(self, "Export", "No analysis loaded.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Export directory")
        if not directory:
            return
        formats = []
        if self.fmt_json.isChecked():
            formats.append("json")
        if self.fmt_md.isChecked():
            formats.append("markdown")
        if self.fmt_html.isChecked():
            formats.append("html")
        if self.fmt_csv.isChecked():
            formats.append("csv")
        if not formats:
            QMessageBox.information(self, "Export", "Select at least one format.")
            return
        try:
            job = export_analysis(
                self._session.result,
                output_dir=directory,
                formats=formats,
                is_demo=self._session.is_demo,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        lines = [f"Wrote {len(job.artifacts)} artifact(s):"]
        for art in job.artifacts:
            lines.append(f"  · {art}")
        if self.fmt_snapshot.isChecked():
            try:
                snap_paths = self._write_snapshot(Path(directory))
                lines.append("Snapshot:")
                for p in snap_paths:
                    lines.append(f"  · {p}")
            except Exception as exc:
                lines.append(f"Snapshot failed: {exc}")
        self.log.setPlainText("\n".join(lines))

    def _write_snapshot(self, output_dir: Path) -> list[Path]:
        """Human-readable + structured Observatory snapshot."""
        import json
        from datetime import datetime, timezone

        from botscope.gui.anomaly import detect_anomalies
        from botscope.gui.dashboard_stats import (
            composition_from_stats,
            explain_composition,
            top_automated_actors,
        )
        from botscope.quality import build_scorecard
        from botscope.statistics.aggregate import aggregate_events

        assert self._session is not None and self._session.result is not None
        events = self._session.filtered_events()
        stats = aggregate_events(events, is_demo=self._session.is_demo)
        den = self._session.denominator
        comp = composition_from_stats(stats, denominator=den)
        actors = top_automated_actors(events)
        anomalies = detect_anomalies(events, denominator=den)
        try:
            quality = build_scorecard(events).to_dict()
        except Exception:
            quality = {}
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset": str(self._session.source_path) if self._session.source_path else None,
            "is_demo": self._session.is_demo,
            "denominator": den,
            "composition": {
                "automated": comp.automated,
                "human_likely": comp.human_likely,
                "unknown": comp.unknown,
                "automated_count": comp.automated_count,
                "human_count": comp.human_count,
                "unknown_count": comp.unknown_count,
                "total": comp.total,
            },
            "top_actors": [a.__dict__ for a in actors],
            "anomalies": [a.to_dict() for a in anomalies],
            "quality": quality,
            "explain": explain_composition(comp, actors),
            "methodology": (
                "Shares are CLASSIFIED over this sensor/dataset only — "
                "not Internet-wide estimates."
            ),
        }
        json_path = output_dir / "observatory_snapshot.json"
        md_path = output_dir / "observatory_snapshot.md"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_lines = [
            "# BotScope Observatory Snapshot",
            "",
            f"- Dataset: `{payload['dataset']}`",
            f"- Demo data: **{payload['is_demo']}**",
            f"- Denominator: {den}",
            "",
            "## Traffic composition",
            f"- Automated: {comp.automated * 100:.1f}% ({comp.automated_count:,})",
            f"- Human-likely: {comp.human_likely * 100:.1f}% ({comp.human_count:,})",
            f"- Unknown: {comp.unknown * 100:.1f}% ({comp.unknown_count:,})",
            "",
            "## Top automated actors",
        ]
        for a in actors[:10]:
            md_lines.append(f"- {a.name}: {a.share * 100:.1f}% ({a.count:,})")
        md_lines += ["", "## Anomalies", ""]
        if not anomalies:
            md_lines.append("No anomalies detected.")
        else:
            for a in anomalies[:20]:
                md_lines.append(
                    f"- [{a.severity}] {a.time_label} · {a.metric}: "
                    f"baseline={a.baseline} observed={a.observed} — {a.reason}"
                )
        md_lines += ["", "## Explain", "", payload["explain"], "", "## Methodology", "", payload["methodology"]]
        md_path.write_text("\n".join(md_lines), encoding="utf-8")
        return [json_path, md_path]


class HistoryPanel(QWidget):
    """Recent .bscope session browser."""

    open_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Session History")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._open_item)
        layout.addWidget(self.list)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.reload)
        open_btn = QPushButton("Open selected")
        open_btn.clicked.connect(self._open_selected)
        row.addWidget(refresh)
        row.addWidget(open_btn)
        layout.addLayout(row)
        self.reload()

    def reload(self) -> None:
        self.list.clear()
        history = SessionHistory().load()
        history.prune_missing()
        for entry in history.recent(30):
            demo = " [DEMO]" if entry.is_demo else ""
            count = f"{entry.event_count:,} events" if entry.event_count is not None else ""
            text = f"{entry.label or entry.path}{demo}\n{entry.opened_at}  {count}\n{entry.path}"
            item = QListWidgetItem(text)
            item.setData(256, entry.path)  # Qt.UserRole
            self.list.addItem(item)

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(256)
        if path:
            self.open_requested.emit(str(path))

    def _open_selected(self) -> None:
        item = self.list.currentItem()
        if item:
            self._open_item(item)


class WorkspacePanel(QWidget):
    """Inspect / apply Analysis Workspace state."""

    apply_requested = Signal(object)  # AnalysisWorkspace

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Analysis Workspace")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "Workspace state (query, denominator, overlays, columns) is saved "
            "inside .bscope as workspace.json."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        layout.addWidget(self.body)
        self._workspace = AnalysisWorkspace()

    def refresh(self, session: GuiSession) -> None:
        self._workspace = session.to_workspace()
        import json

        self.body.setPlainText(json.dumps(self._workspace.to_dict(), indent=2))


class LiveFeedPanel(QWidget):
    """Authorize and control live log-tail / packet capture feeds."""

    start_requested = Signal(str)  # log path
    start_pcap_file_requested = Signal(str)  # offline pcap path → analyze
    start_iface_requested = Signal(str, str)  # interface, bpf
    stop_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("Live / Capture (authorized)")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        warn = QLabel(
            "Requires explicit authorization. Local files/interfaces only — "
            "no third-party scanning. Payloads are not retained as content. "
            "Sensor ● LIVE only while an authorized feed runs. Rates are measured."
        )
        warn.setObjectName("muted")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        # Log tail
        layout.addWidget(QLabel("Access log tail"))
        self.path = QLineEdit()
        self.path.setPlaceholderText("Path to authorized access log…")
        browse = QPushButton("Browse log…")
        browse.clicked.connect(self._browse)
        row = QHBoxLayout()
        row.addWidget(self.path)
        row.addWidget(browse)
        layout.addLayout(row)

        # Offline PCAP
        layout.addWidget(QLabel("Offline PCAP / PCAPNG"))
        self.pcap_path = QLineEdit()
        self.pcap_path.setPlaceholderText("Path to authorized capture file…")
        browse_pcap = QPushButton("Browse PCAP…")
        browse_pcap.clicked.connect(self._browse_pcap)
        row_p = QHBoxLayout()
        row_p.addWidget(self.pcap_path)
        row_p.addWidget(browse_pcap)
        layout.addLayout(row_p)
        open_pcap = QPushButton("Analyze PCAP (offline)")
        open_pcap.clicked.connect(self._open_pcap)
        layout.addWidget(open_pcap)

        # Live iface
        layout.addWidget(QLabel("Live interface sniff (requires botscope[capture])"))
        self.iface = QLineEdit()
        self.iface.setPlaceholderText("Interface name (from status below)")
        self.bpf = QLineEdit()
        self.bpf.setPlaceholderText("Optional BPF filter, e.g. tcp port 80")
        layout.addWidget(self.iface)
        layout.addWidget(self.bpf)
        refresh_if = QPushButton("Refresh interface list / capture status")
        refresh_if.clicked.connect(self._refresh_status)
        layout.addWidget(refresh_if)

        self.authorize = QCheckBox(
            "I authorize BotScope to observe this local source (log / interface)"
        )
        layout.addWidget(self.authorize)

        btns = QHBoxLayout()
        start = QPushButton("Start live log tail")
        start_cap = QPushButton("Start live interface capture")
        stop = QPushButton("Stop")
        start.clicked.connect(self._start)
        start_cap.clicked.connect(self._start_iface)
        stop.clicked.connect(self.stop_requested.emit)
        btns.addWidget(start)
        btns.addWidget(start_cap)
        btns.addWidget(stop)
        layout.addLayout(btns)

        self.status = QPlainTextEdit()
        self.status.setReadOnly(True)
        self.status.setPlainText("Idle — not live.")
        layout.addWidget(self.status)

        layout.addWidget(QLabel("Alerts (local thresholds)"))
        self.alerts = QPlainTextEdit()
        self.alerts.setReadOnly(True)
        self.alerts.setMaximumHeight(120)
        self.alerts.setPlainText("No alerts.")
        layout.addWidget(self.alerts)

        fan_note = QLabel(
            "Start log tail and/or interface capture together — events fan into one "
            "Observatory stream with sensor_id tags. Live batches persist to a .bscope."
        )
        fan_note.setObjectName("muted")
        fan_note.setWordWrap(True)
        layout.addWidget(fan_note)
        self._refresh_status()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Authorized access log",
            "",
            "Logs (*.log *.txt *.json *.jsonl *.ndjson);;All files (*.*)",
        )
        if path:
            self.path.setText(path)

    def _browse_pcap(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Authorized PCAP",
            "",
            "Captures (*.pcap *.pcapng *.cap);;All files (*.*)",
        )
        if path:
            self.pcap_path.setText(path)

    def _open_pcap(self) -> None:
        path = self.pcap_path.text().strip()
        if not path:
            QMessageBox.information(self, "PCAP", "Select a capture file.")
            return
        self.start_pcap_file_requested.emit(path)

    def _start(self) -> None:
        if not self.authorize.isChecked():
            QMessageBox.warning(
                self,
                "Authorization required",
                "Check the authorization box before starting a live feed.",
            )
            return
        path = self.path.text().strip()
        if not path:
            QMessageBox.information(self, "Live feed", "Select a log file.")
            return
        self.start_requested.emit(path)

    def _start_iface(self) -> None:
        if not self.authorize.isChecked():
            QMessageBox.warning(
                self,
                "Authorization required",
                "Check the authorization box before starting interface capture.",
            )
            return
        iface = self.iface.text().strip()
        if not iface:
            QMessageBox.information(self, "Live capture", "Enter a local interface name.")
            return
        self.start_iface_requested.emit(iface, self.bpf.text().strip())

    def _refresh_status(self) -> None:
        from botscope.capture import live_capture_status

        st = live_capture_status()
        lines = [
            f"scapy: {'yes' if st.get('scapy_available') else 'no — pip install botscope[capture]'}",
            f"live_capture: {st.get('live_capture')}",
            st.get("policy", ""),
            "",
            "Interfaces:",
        ]
        ifaces = st.get("interfaces") or []
        if not ifaces:
            lines.append("  (none listed — install scapy or check permissions)")
        for item in ifaces:
            lines.append(f"  • {item.get('name')}")
        self.status.setPlainText("\n".join(lines))

    def set_status_text(self, text: str) -> None:
        self.status.setPlainText(text)

    def append_alerts(self, alerts) -> None:
        lines = []
        for alert in alerts:
            lines.append(f"[{alert.severity.value}] {alert.message}")
        existing = self.alerts.toPlainText().strip()
        if existing == "No alerts.":
            existing = ""
        block = "\n".join(lines)
        self.alerts.setPlainText((existing + "\n" + block).strip() if existing else block)
