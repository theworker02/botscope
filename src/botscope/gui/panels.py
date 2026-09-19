"""Observatory workspace panels — rendered with native Qt widgets."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from botscope.botcard import load_library
from botscope.classify.result import RULESET_VERSION
from botscope.gui.anomaly import detect_anomalies
from botscope.gui.breakdown import available_dimensions, breakdown
from botscope.gui.dashboard_stats import (
    build_traffic_pulse,
    composition_from_stats,
    confidence_distribution,
    explain_composition,
    metric_provenance,
    top_automated_actors,
)
from botscope.gui.dashboard_widgets import (
    ConfidencePanel,
    ExplainPanel,
    KpiCard,
    ShareRing,
    TopActorsPanel,
    TrafficPulsePanel,
)
from botscope.gui.events_model import EventsTableModel
from botscope.gui.interactive import ActorOrbit, ZeroConfigBanner
from botscope.gui.motion import stagger_fade
from botscope.gui.phase6_widgets import (
    AnomalyPanel,
    BreakdownExplorer,
    FilterChipBar,
    install_stat_copy_menu,
)
from botscope.gui.session_state import GuiSession
from botscope.gui.widgets import CategoryBars, MetricTile, TimelineChart, fmt_int, fmt_pct
from botscope.live import ObservatorySnapshot
from botscope.provenance import inspect_event, summarize_corpus
from botscope.quality import build_scorecard


class _ClickFilter(QObject):
    def __init__(self, callback) -> None:
        super().__init__()
        self._callback = callback

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.MouseButtonPress:
            self._callback()
            return True
        return False


class ObservatoryPanel(QWidget):
    """Primary dashboard: KPI shares, ring, pulse, actors, confidence, timeline."""

    denominator_changed = Signal(str)
    filter_requested = Signal(str)  # classification family key
    actor_requested = Signal(str)
    provenance_requested = Signal(object)  # provenance dict
    clear_filters = Signal()
    remove_filter = Signal(str)
    anomaly_time_requested = Signal(str)
    breakdown_row_requested = Signal(str, str)
    sources_requested = Signal()
    timeline_bucket_requested = Signal(str)
    category_bar_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("BotScope Observatory")
        title.setObjectName("pageHeader")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Denominator:"))
        self.denominator = QComboBox()
        self.denominator.addItems(["requests", "bytes"])
        self.denominator.setToolTip(
            "Shares use this denominator consistently. "
            "Request % and byte % are different concepts — never mix unlabeled."
        )
        self.denominator.currentTextChanged.connect(self.denominator_changed.emit)
        header.addWidget(self.denominator)
        layout.addLayout(header)

        self.demo_banner = QLabel("DEMO DATA — synthetic corpus, not real measurements")
        self.demo_banner.setObjectName("demoBanner")
        self.demo_banner.hide()
        layout.addWidget(self.demo_banner)

        self.zero_banner = ZeroConfigBanner()
        layout.addWidget(self.zero_banner)

        self.filter_chips = FilterChipBar()
        self.filter_chips.clear_all.connect(self.clear_filters.emit)
        self.filter_chips.chip_removed.connect(self.remove_filter.emit)
        layout.addWidget(self.filter_chips)

        coverage_row = QHBoxLayout()
        self.tile_sources = MetricTile("Source coverage", provenance="INFERRED")
        self.tile_sources.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tile_sources.setToolTip("Click to open Source Health")
        coverage_row.addWidget(self.tile_sources)
        coverage_row.addStretch()
        layout.addLayout(coverage_row)
        self._sources_click_filter = _ClickFilter(lambda: self.sources_requested.emit())
        self.tile_sources.installEventFilter(self._sources_click_filter)

        metrics = QHBoxLayout()
        self.kpi_auto = KpiCard(
            "automated",
            "Automated",
            tooltip="Share of eligible traffic classified into automation categories.",
        )
        self.kpi_human = KpiCard(
            "human_likely",
            "Human-likely",
            tooltip="Share classified HUMAN-LIKELY from browser-like evidence.",
        )
        self.kpi_unknown = KpiCard(
            "unknown",
            "Unknown",
            tooltip="Share left UNKNOWN — a valid scientific outcome.",
        )
        for card in (self.kpi_auto, self.kpi_human, self.kpi_unknown):
            card.clicked.connect(self.filter_requested.emit)
            metrics.addWidget(card)
        layout.addLayout(metrics)
        self._install_kpi_menus()

        compact = QHBoxLayout()
        self.tile_events = MetricTile("Total requests", provenance="OBSERVED")
        self.tile_bytes = MetricTile("Total bytes", provenance="OBSERVED")
        self.tile_quality = MetricTile("Dataset quality", provenance="INFERRED")
        self.tile_period = MetricTile("Observation period", provenance="OBSERVED")
        for tile in (self.tile_events, self.tile_bytes, self.tile_quality, self.tile_period):
            compact.addWidget(tile)
        layout.addLayout(compact)

        note = QLabel(
            "Shares are CLASSIFIED aggregates over this sensor/source only — "
            "not an Internet-wide estimate. Click a KPI or ring segment to filter Events. "
            "Right-click a KPI to copy value / context / provenance."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        mid = QHBoxLayout()
        left = QVBoxLayout()
        self.ring = ShareRing()
        self.ring.segment_clicked.connect(self.filter_requested.emit)
        left.addWidget(self.ring, stretch=2)
        self.pulse = TrafficPulsePanel()
        left.addWidget(self.pulse, stretch=1)
        mid.addLayout(left, stretch=2)

        right = QVBoxLayout()
        self.actors = TopActorsPanel()
        self.actors.actor_selected.connect(self.actor_requested.emit)
        right.addWidget(self.actors, stretch=1)
        self.orbit = ActorOrbit()
        self.orbit.actor_clicked.connect(self.actor_requested.emit)
        right.addWidget(self.orbit, stretch=1)
        self.confidence = ConfidencePanel()
        right.addWidget(self.confidence, stretch=1)
        mid.addLayout(right, stretch=2)
        layout.addLayout(mid, stretch=3)

        lower = QHBoxLayout()
        self.breakdown = BreakdownExplorer()
        self.breakdown.set_dimension_handler(lambda _t: self._refresh_breakdown_only())
        self.breakdown.row_selected.connect(self.breakdown_row_requested.emit)
        lower.addWidget(self.breakdown, stretch=2)
        self.anomalies = AnomalyPanel()
        self.anomalies.anomaly_selected.connect(self.anomaly_time_requested.emit)
        lower.addWidget(self.anomalies, stretch=2)
        layout.addLayout(lower, stretch=2)

        self.timeline = TimelineChart()
        self.timeline.bucket_clicked.connect(self.timeline_bucket_requested.emit)
        layout.addWidget(self.timeline, stretch=2)

        self.categories = CategoryBars()
        self.categories.category_clicked.connect(self.category_bar_requested.emit)
        layout.addWidget(self.categories, stretch=1)

        self.explain = ExplainPanel()
        self.explain.why_btn.clicked.connect(self._emit_provenance)
        layout.addWidget(self.explain)
        self._last_provenance: dict | None = None
        self._last_comp = None
        self._session_ref: GuiSession | None = None
        self._source_coverage_text = "— / —"

        self.empty_cta = QWidget()
        self.empty_cta.setObjectName("emptyState")
        empty_layout = QVBoxLayout(self.empty_cta)
        empty_layout.setContentsMargins(20, 18, 20, 18)
        empty_msg = QLabel(
            "No dataset loaded.\n"
            "Open a web log or PCAP, load sample data, or open Global Observatory."
        )
        empty_msg.setObjectName("muted")
        empty_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_msg.setWordWrap(True)
        empty_layout.addWidget(empty_msg)
        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("Open dataset")
        self.btn_open.setObjectName("primaryButton")
        self.btn_demo = QPushButton("Load sample data")
        self.btn_demo.setObjectName("ghostButton")
        self.btn_global = QPushButton("Learn / Global sources")
        for b in (self.btn_open, self.btn_demo, self.btn_global):
            btn_row.addWidget(b)
        btn_row.addStretch()
        empty_layout.addLayout(btn_row)
        layout.addWidget(self.empty_cta)
        self._empty_animated = False

    def _emit_provenance(self) -> None:
        if self._last_provenance:
            self.provenance_requested.emit(self._last_provenance)

    def _install_kpi_menus(self) -> None:
        def ctx_for(key: str, title: str):
            def value_fn() -> str:
                card = {"automated": self.kpi_auto, "human_likely": self.kpi_human, "unknown": self.kpi_unknown}[
                    key
                ]
                return card.value.text()

            def context_fn() -> str:
                if self._last_comp is None:
                    return value_fn()
                den = self._last_comp.denominator
                share = {
                    "automated": self._last_comp.automated,
                    "human_likely": self._last_comp.human_likely,
                    "unknown": self._last_comp.unknown,
                }[key]
                return (
                    f"{title} traffic represented {share * 100:.1f}% of eligible {den} "
                    f"in the selected dataset/time range."
                )

            def provenance_fn() -> str:
                import json

                return json.dumps(self._last_provenance or {}, indent=2)

            return value_fn, context_fn, provenance_fn

        for key, title, card in (
            ("automated", "Automated", self.kpi_auto),
            ("human_likely", "Human-likely", self.kpi_human),
            ("unknown", "Unknown", self.kpi_unknown),
        ):
            vf, cf, pf = ctx_for(key, title)
            install_stat_copy_menu(card, value_fn=vf, context_fn=cf, provenance_fn=pf)

    def set_source_coverage(self, available: int, total: int, active: int = 0) -> None:
        self._source_coverage_text = f"{available} / {total}"
        detail = f"{active} contributed" if active else "click for Source Health"
        self.tile_sources.set_value(f"{available}/{total}", "INFERRED")
        self.tile_sources.setToolTip(
            f"SOURCE COVERAGE\n{available} / {total} available\n"
            f"{active} contributed to this analysis\n{detail}"
        )

    def _refresh_breakdown_only(self) -> None:
        if self._session_ref is None or not self._session_ref.loaded:
            return
        events = self._session_ref.filtered_events()
        dims = available_dimensions(events)
        dim = self.breakdown.current_dimension()
        if dim not in dims and dims:
            dim = dims[0]
        self.breakdown.set_dimensions(dims, dim)
        family = self._session_ref.filter_category if self._session_ref.filter_category in {
            "automated",
            "human_likely",
            "unknown",
        } else None
        rows = breakdown(events, dimension=dim or "classification", family=family)
        crumb = f"Family: {family}" if family else "All traffic"
        self.breakdown.set_rows(rows, crumb=crumb)

    def refresh(self, session: GuiSession) -> None:
        self._session_ref = session
        if session.is_demo or (session.stats and session.stats.is_demo):
            self.demo_banner.show()
        else:
            self.demo_banner.hide()

        stats = session.stats
        if stats is None:
            self.kpi_auto.set_share(None, 0)
            self.kpi_human.set_share(None, 0)
            self.kpi_unknown.set_share(None, 0)
            self.tile_events.set_value("—", "OBSERVED")
            self.tile_bytes.set_value("—", "OBSERVED")
            self.tile_quality.set_value("—", "INFERRED")
            self.tile_period.set_value("—", "OBSERVED")
            self.tile_sources.set_value("—", "INFERRED")
            self.ring.set_composition(None)
            self.pulse.set_pulse(None)
            self.actors.set_actors([])
            self.orbit.set_actors([])
            self.confidence.set_buckets([])
            self.explain.set_text("Load a dataset to explain this view.")
            self.timeline.set_series([])
            self.categories.set_items([])
            self.anomalies.set_findings([])
            self.breakdown.set_dimensions([])
            self.breakdown.set_rows([])
            self.filter_chips.set_chips([])
            self.empty_cta.show()
            if not self._empty_animated:
                self._empty_animated = True
                stagger_fade(
                    [self.btn_open, self.btn_demo, self.btn_global],
                    per_item_ms=180,
                    stagger_ms=50,
                )
            return

        self.empty_cta.hide()
        den = session.denominator
        events = session.filtered_events()
        from botscope.statistics.aggregate import aggregate_events

        view_stats = aggregate_events(events, is_demo=session.is_demo) if events else stats
        comp = composition_from_stats(view_stats, denominator=den)
        self._last_comp = comp
        self.kpi_auto.set_share(comp.automated, comp.automated_count)
        self.kpi_human.set_share(comp.human_likely, comp.human_count)
        self.kpi_unknown.set_share(comp.unknown, comp.unknown_count)
        self.tile_events.set_value(fmt_int(view_stats.total_events), "OBSERVED")
        self.tile_bytes.set_value(fmt_int(view_stats.total_bytes), "OBSERVED")

        try:
            scorecard = build_scorecard(events)
            if scorecard.dimensions:
                order = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}
                worst = min(
                    scorecard.dimensions,
                    key=lambda d: order.get(d.label, 1),
                )
                display = {
                    "excellent": "Excellent",
                    "good": "Good",
                    "fair": "Limited",
                    "poor": "Poor",
                }.get(worst.label, worst.label.title())
                self.tile_quality.set_value(display, "INFERRED")
                tip = "\n".join(
                    f"{d.name}: {d.label} — {d.rationale}" for d in scorecard.dimensions
                )
                self.tile_quality.setToolTip(
                    "Multi-dimension quality (worst dimension shown as headline):\n" + tip
                )
            else:
                self.tile_quality.set_value("—", "INFERRED")
        except Exception:  # noqa: BLE001
            self.tile_quality.set_value("—", "INFERRED")

        timestamps = [e.timestamp for e in events if e.timestamp]
        if timestamps:
            period = f"{min(timestamps).date()} → {max(timestamps).date()}"
        else:
            period = "—"
        self.tile_period.set_value(period, "OBSERVED")

        self.ring.set_composition(comp)
        actors = top_automated_actors(events)
        self.actors.set_actors(actors)
        self.orbit.set_actors([(a.name, a.share) for a in actors])
        self.confidence.set_buckets(confidence_distribution(events))
        self.pulse.set_pulse(build_traffic_pulse(events, denominator=den))
        self.explain.set_text(explain_composition(comp, actors))
        self._last_provenance = metric_provenance(
            metric=f"Automated {den} share",
            numerator=comp.automated_count,
            denominator=comp.total,
            denominator_label=f"eligible {den}",
            sources=[str(session.source_path)] if session.source_path else ["local sensor"],
            filters=[f for f in [session.filter_category, session.filter_text, session.query] if f],
            time_range=str(session.time_range),
            ruleset_version=RULESET_VERSION,
            is_demo=session.is_demo,
        )
        self.timeline.set_series(view_stats.timeline)
        self.categories.set_items(list(view_stats.by_category.items()))

        try:
            self.anomalies.set_findings(detect_anomalies(events, denominator=den))
        except Exception:  # noqa: BLE001
            self.anomalies.set_findings([])

        self._refresh_breakdown_only()

        chips: list[tuple[str, str]] = []
        if session.filter_category:
            chips.append(("category", session.filter_category.replace("_", " ")))
        if session.filter_text:
            chips.append(("text", f"search:{session.filter_text}"))
        if session.query:
            chips.append(("query", f"query:{session.query[:40]}"))
        if session.time_range.start or session.time_range.end:
            chips.append(("time", "custom time range"))
        self.filter_chips.set_chips(chips)

    def apply_snapshot(self, snap: ObservatorySnapshot) -> None:
        """Update dashboard from a bounded live snapshot (not per-event signals)."""
        if snap.is_demo:
            self.demo_banner.show()
        self.empty_cta.hide()
        total = snap.total_events or 0
        auto_n = int((snap.automated_share or 0) * total)
        human_n = int((snap.human_share or 0) * total)
        unk_n = int((snap.unknown_share or 0) * total)
        self.kpi_auto.set_share(snap.automated_share, auto_n)
        self.kpi_human.set_share(snap.human_share, human_n)
        self.kpi_unknown.set_share(snap.unknown_share, unk_n)
        self.tile_events.set_value(fmt_int(snap.total_events), "OBSERVED")
        self.timeline.set_series(list(snap.timeline))
        self.categories.set_items(list(snap.by_category.items()))
        from botscope.gui.dashboard_stats import CompositionShare

        self.ring.set_composition(
            CompositionShare(
                automated=snap.automated_share or 0.0,
                human_likely=snap.human_share or 0.0,
                unknown=snap.unknown_share or 0.0,
                automated_count=auto_n,
                human_count=human_n,
                unknown_count=unk_n,
                total=total,
                denominator="requests",
            )
        )


class InspectorPanel(QWidget):
    """Classification inspector with evidence for/against."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Classification Inspector")
        title.setObjectName("pageHeader")
        layout.addWidget(title)

        form = QFormLayout()
        self.category = QLabel("—")
        self.confidence = QLabel("—")
        self.attribution = QLabel("—")
        self.identity = QLabel("—")
        self.provenance = QLabel("—")
        form.addRow("Category:", self.category)
        form.addRow("Confidence:", self.confidence)
        form.addRow("Attribution:", self.attribution)
        form.addRow("Identity:", self.identity)
        form.addRow("Provenance:", self.provenance)
        layout.addLayout(form)

        conf_note = QLabel(
            "v2 confidence is a heuristic score or ML model probability with evidence — "
            "not a calibrated probability."
        )
        conf_note.setObjectName("muted")
        conf_note.setWordWrap(True)
        layout.addWidget(conf_note)

        self.evidence = QPlainTextEdit()
        self.evidence.setReadOnly(True)
        layout.addWidget(self.evidence, stretch=1)

        copy_row = QHBoxLayout()
        copy_ev = QPushButton("Copy evidence")
        copy_ev.clicked.connect(self._copy_evidence)
        copy_all = QPushButton("Copy inspector summary")
        copy_all.clicked.connect(self._copy_summary)
        copy_row.addWidget(copy_ev)
        copy_row.addWidget(copy_all)
        layout.addLayout(copy_row)

        self.request_meta = QPlainTextEdit()
        self.request_meta.setReadOnly(True)
        self.request_meta.setMaximumHeight(140)
        layout.addWidget(self.request_meta)
        self._summary_text = ""

    def clear(self) -> None:
        self.category.setText("—")
        self.confidence.setText("—")
        self.attribution.setText("—")
        self.identity.setText("—")
        self.provenance.setText("—")
        self.evidence.setPlainText("Select an event to inspect classification evidence.")
        self.request_meta.clear()

    def show_event(self, session: GuiSession) -> None:
        event = session.selected_event()
        if event is None:
            self.clear()
            return
        extras = event.extras or {}
        self.category.setText(event.classification or "UNKNOWN")
        conf = event.confidence
        self.confidence.setText(f"{conf:.2f}" if conf is not None else "—")
        self.attribution.setText(str(extras.get("attribution") or "none (not verified)"))
        self.identity.setText(str(extras.get("identity_status") or "—"))
        self.provenance.setText(event.provenance.value if event.provenance else "—")

        lines = ["Evidence", "─" * 32, ""]
        for item in event.evidence:
            lines.append(item)
        if extras.get("matched_rules"):
            lines += ["", "Matched rules:", ", ".join(extras["matched_rules"])]
        if extras.get("confidence_note"):
            lines += ["", str(extras["confidence_note"])]
        self.evidence.setPlainText("\n".join(lines))

        meta = [
            f"time: {event.timestamp.isoformat()}",
            f"src: {event.src_address}",
            f"method: {event.http_method}  path: {event.path}",
            f"status: {event.status}  bytes_out: {event.bytes_out}",
            f"ua: {event.user_agent}",
        ]
        self.request_meta.setPlainText("\n".join(meta))
        self._summary_text = "\n".join(
            [
                f"Category: {self.category.text()}",
                f"Confidence: {self.confidence.text()}",
                f"Attribution: {self.attribution.text()}",
                f"Identity: {self.identity.text()}",
                f"Provenance: {self.provenance.text()}",
                "",
                self.evidence.toPlainText(),
                "",
                self.request_meta.toPlainText(),
            ]
        )

    def _copy_evidence(self) -> None:
        QGuiApplication.clipboard().setText(self.evidence.toPlainText())

    def _copy_summary(self) -> None:
        QGuiApplication.clipboard().setText(self._summary_text or self.evidence.toPlainText())


class EventsPanel(QWidget):
    """Virtualized events browser (QAbstractTableModel + QTableView).

    Architecture note: there is no hard 5k-row presentation wall. The model
    holds references; ``data()`` returns cells on demand. Filtered views may
    still materialize an index list in memory — prefer query filters for
    multi-million corpora rather than copying into QTableWidgetItems.
    """

    event_selected = Signal(str)
    query_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Events")
        title.setObjectName("pageHeader")
        layout.addWidget(title)

        filt = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Quick search path / UA / IP / category…")
        self.query = QLineEdit()
        self.query.setPlaceholderText(
            'Query: classification eq "AI CRAWLER" AND confidence gte 0.5'
        )
        self.category = QComboBox()
        self.category.addItem("All categories", None)
        filt.addWidget(self.search, stretch=1)
        filt.addWidget(self.category, stretch=1)
        layout.addLayout(filt)
        layout.addWidget(self.query)

        self.model = EventsTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.selectionModel().selectionChanged.connect(self._on_select)
        layout.addWidget(self.table)

        self.status = QLabel("")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)

        self.query.editingFinished.connect(self.query_changed.emit)

    def refresh(self, session: GuiSession) -> None:
        current = self.category.currentData()
        cats = sorted({e.classification or "UNKNOWN" for e in session.events})
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("All categories", None)
        for cat in cats:
            self.category.addItem(cat, cat)
        idx = self.category.findData(current)
        self.category.setCurrentIndex(max(0, idx))
        self.category.blockSignals(False)

        if self.query.text() != session.query:
            self.query.blockSignals(True)
            self.query.setText(session.query)
            self.query.blockSignals(False)

        events = session.filtered_events()
        self.model.set_events(events)
        self.table.resizeColumnsToContents()
        total = len(session.events)
        shown = len(events)
        self.status.setText(
            f"Showing {shown:,} of {total:,} events (virtualized model — no 5k hard cap)."
        )

    def _on_select(self, *_args) -> None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        event_id = self.model.event_id_at(row)
        if event_id:
            self.event_selected.emit(event_id)


class QualityPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Dataset Health")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "Dimensions are reported separately. BotScope does not collapse "
            "quality into one misleading percentage."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Dimension", "Label", "Score", "Rationale"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.interpretation = QPlainTextEdit()
        self.interpretation.setReadOnly(True)
        self.interpretation.setMaximumHeight(120)
        layout.addWidget(self.interpretation)

    def refresh(self, session: GuiSession) -> None:
        if not session.events:
            self.table.setRowCount(0)
            self.interpretation.setPlainText("Load a dataset to evaluate health.")
            return
        card = build_scorecard(session.events)
        self.table.setRowCount(len(card.dimensions))
        for row, dim in enumerate(card.dimensions):
            self.table.setItem(row, 0, QTableWidgetItem(dim.name))
            self.table.setItem(row, 1, QTableWidgetItem(dim.label))
            self.table.setItem(row, 2, QTableWidgetItem(f"{dim.score:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(dim.rationale))
        self.table.resizeColumnsToContents()

        evidence = card.dimension("evidence_coverage")
        completeness = card.dimension("completeness")
        lines = [
            f"Events evaluated: {card.event_count:,}",
            "",
            "Interpretation:",
        ]
        if completeness and completeness.score >= 0.65:
            lines.append("• Suitable for request-volume analysis.")
        else:
            lines.append("• Weak for volume analysis — improve field completeness.")
        if evidence and evidence.score >= 0.5:
            lines.append("• Moderate support for classification review.")
        else:
            lines.append("• Weak for bot attribution — identity signals limited.")
        lines.extend([""] + card.notes)
        self.interpretation.setPlainText("\n".join(lines))


class ProvenancePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Measurement Provenance")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        layout.addWidget(self.body)

    def refresh(self, session: GuiSession) -> None:
        if not session.events:
            self.body.setPlainText("No measurements loaded.")
            return
        summary = summarize_corpus(session.events)
        shares = session.share_payload()
        lines = [
            "Where did these numbers come from?",
            "─" * 40,
            f"Source: {session.source_path or '(in-memory / demo)'}",
            f"Events: {len(session.events):,}",
            f"Demo: {'YES — DEMO DATA' if session.is_demo else 'no'}",
            "",
            "Automated request share",
            f"  value: {fmt_pct(shares.get('automated'))}",
            f"  provenance: {shares.get('provenance')}",
            f"  denominator: {shares.get('denominator')}",
            "  method: direct aggregation of CLASSIFIED events",
            "",
            "Corpus provenance summary",
            f"  {summary.to_dict() if hasattr(summary, 'to_dict') else summary}",
        ]
        event = session.selected_event()
        if event is not None:
            report = inspect_event(event)
            lines += [
                "",
                f"Selected event {event.event_id}",
                f"  event-level provenance: {report.event_level.value}",
                f"  evidence items: {report.evidence_count}",
            ]
            for field in report.fields:
                if field.present:
                    lines.append(
                        f"  • {field.field}: {field.level.value} ({field.role.value})"
                    )
        self.body.setPlainText("\n".join(str(x) for x in lines))


class BotLibraryPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        title = QLabel("Bot Library")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "KNOWN signatures from the bundled database — distinct from OBSERVED "
            "in the current dataset. User-Agent alone does not verify identity."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        split = QSplitter()
        self.list = QListWidget()
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        split.addWidget(self.list)
        split.addWidget(self.detail)
        split.setStretchFactor(1, 2)
        layout.addWidget(split)

        self._cards = load_library().cards
        for card in self._cards:
            item = QListWidgetItem(f"{card.name}  ·  {card.category}")
            item.setData(Qt.ItemDataRole.UserRole, card.name)
            self.list.addItem(item)
        self.list.currentRowChanged.connect(self._show_card)
        if self._cards:
            self.list.setCurrentRow(0)

    def _show_card(self, row: int) -> None:
        if row < 0 or row >= len(self._cards):
            return
        card = self._cards[row]
        lines = [
            f"Name: {card.name}",
            f"Category: {card.category}",
            f"Confidence (signature prior): {card.confidence:.2f}",
            f"Verification: {card.verification_method}",
            f"Source: {card.source}",
            f"Date checked: {card.date_checked}",
            "",
            "Evidence:",
            *[f"  • {e}" for e in card.evidence],
            "",
            "UA patterns:",
            *[f"  • {p}" for p in card.ua_patterns],
            "",
            card.identity_caveat,
            "",
            card.notes,
        ]
        self.detail.setPlainText("\n".join(lines))

    def mark_observed(self, session: GuiSession) -> None:
        """Annotate list items that appear in the loaded dataset."""
        observed_uas = " ".join((e.user_agent or "").lower() for e in session.events)
        for i, card in enumerate(self._cards):
            hit = any(p.lower() in observed_uas for p in card.ua_patterns)
            label = f"{card.name}  ·  {card.category}"
            if hit:
                label += "  [OBSERVED IN DATASET]"
            self.list.item(i).setText(label)
