"""BotScope Observatory main window — native desktop shell (Qt/PySide6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from botscope.__version__ import __version__
from botscope.api.analyzer import AnalysisResult
from botscope.demo import DEMO_NOTICE, ensure_demo_log
from botscope.gui.global_observatory import GlobalObservatoryPanel
from botscope.gui.motion import fade_in, set_reduce_motion
from botscope.gui.navigation import PRIMARY_PAGES, page_index, resolve_page_id
from botscope.gui.panels import (
    BotLibraryPanel,
    EventsPanel,
    InspectorPanel,
    ObservatoryPanel,
    ProvenancePanel,
    QualityPanel,
)
from botscope.gui.session_io import (
    load_analysis_session,
    save_analysis_session,
    suggest_session_name,
)
from botscope.gui.session_state import GuiSession
from botscope.gui.settings_panel import SettingsPanel
from botscope.gui.sources_panel import SourcesRegistryPanel
from botscope.gui.theme import set_chart_theme, stylesheet_for
from botscope.gui.welcome import WelcomeAction, WelcomeDialog
from botscope.gui.workers import AnalyzeWorker, LiveLogTailWorker, LivePacketCaptureWorker
from botscope.gui.workstation_panels import (
    AnnotationsPanel,
    ClassifierComparePanel,
    ComparePanel,
    ExportPanel,
    HistoryPanel,
    LiveFeedPanel,
    WorkspacePanel,
)
from botscope.live import ObservatorySnapshot
from botscope.privacy.transforms import PrivacyConfig
from botscope.query import QueryError
from botscope.statistics.aggregate import aggregate_events
from botscope.ux import (
    AppSettings,
    RecentFiles,
    classify_path,
    load_settings,
)
from botscope.workspace import TimeRange


class ObservatoryWindow(QMainWindow):
    """Scientific observatory workspace rendered entirely with native widgets."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f"BotScope Observatory  ·  v{__version__}")
        self.resize(1480, 920)
        self.setAcceptDrops(True)
        self.settings = settings or load_settings()
        set_reduce_motion(getattr(self.settings, "reduce_motion", False))
        set_chart_theme(self.settings.theme)
        self.recents = RecentFiles().load()
        self.session = GuiSession()
        self.session.denominator = self.settings.default_denominator
        self._worker: AnalyzeWorker | None = None
        self._live_workers: list = []
        self._live_writer = None
        self._fanin = None
        self._alert_engine = None

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_status()
        self._set_empty_state()
        self._rebuild_recent_menu()

    # ── menus / chrome ───────────────────────────────────────────────

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        act_open = QAction("Open Web &Log…", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.open_log)
        file_menu.addAction(act_open)

        act_session = QAction("Open &Session (.bscope)…", self)
        act_session.triggered.connect(self.open_session)
        file_menu.addAction(act_session)

        act_demo = QAction("Load &Demo Data", self)
        act_demo.triggered.connect(self.load_demo)
        file_menu.addAction(act_demo)

        file_menu.addSeparator()
        act_save = QAction("&Save Session", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.save_session)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save Session &As…", self)
        act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        act_save_as.triggered.connect(self.save_session_as)
        file_menu.addAction(act_save_as)

        act_history = QAction("Session &History…", self)
        act_history.triggered.connect(lambda: self._goto_nav("History"))
        file_menu.addAction(act_history)

        self._recent_menu = file_menu.addMenu("Open &Recent")
        self._rebuild_recent_menu()

        file_menu.addSeparator()
        act_export = QAction("Quick Export Markdown…", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self.quick_export_markdown)
        file_menu.addAction(act_export)

        file_menu.addSeparator()
        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        view_menu = self.menuBar().addMenu("&View")
        for page in PRIMARY_PAGES:
            act = QAction(page.label, self)
            act.setToolTip(page.tooltip)
            act.triggered.connect(
                lambda checked=False, pid=page.id: self._goto_page(pid)
            )
            view_menu.addAction(act)

        act_settings = QAction("&Settings…", self)
        act_settings.setShortcut("Ctrl+,")
        act_settings.triggered.connect(lambda: self._goto_page("settings"))
        view_menu.addSeparator()
        view_menu.addAction(act_settings)

        help_menu = self.menuBar().addMenu("&Help")
        act_welcome = QAction("Welcome…", self)
        act_welcome.triggered.connect(self.show_welcome)
        help_menu.addAction(act_welcome)
        act_about = QAction("About BotScope", self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)
        act_method = QAction("Methodology…", self)
        act_method.triggered.connect(self.show_methodology)
        help_menu.addAction(act_method)
        act_glossary = QAction("Glossary…", self)
        act_glossary.triggered.connect(self.show_glossary)
        help_menu.addAction(act_glossary)
        act_diag = QAction("Diagnostics…", self)
        act_diag.triggered.connect(self.show_diagnostics)
        help_menu.addAction(act_diag)
    def _build_toolbar(self) -> None:
        bar = QToolBar("Main")
        bar.setMovable(False)
        self.addToolBar(bar)
        for text, slot in (
            ("Open", self.open_log),
            ("Demo", self.load_demo),
            ("Session", self.open_session),
            ("Save", self.save_session),
            ("Export MD", self.quick_export_markdown),
            ("Global", lambda: self._goto_page("global")),
        ):
            act = QAction(text, self)
            act.triggered.connect(slot)
            bar.addAction(act)

        bar.addSeparator()
        bar.addWidget(QLabel(" Range:"))
        self.range_combo = QComboBox()
        self.range_combo.addItem("Entire dataset", "all")
        self.range_combo.addItem("Last 24 hours", "24h")
        self.range_combo.addItem("Last 7 days", "7d")
        self.range_combo.addItem("Last 30 days", "30d")
        self.range_combo.setToolTip("Global observation window applied to dashboard & Events")
        self.range_combo.currentIndexChanged.connect(self._on_global_range)
        bar.addWidget(self.range_combo)

    def _build_body(self) -> None:
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter()
        outer.addWidget(splitter)

        nav_wrap = QWidget()
        nav_wrap.setObjectName("navChrome")
        nav_layout = QVBoxLayout(nav_wrap)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 8, 0)
        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand = QLabel("BotScope")
        brand.setObjectName("brandWordmark")
        brand_col.addWidget(brand)
        tagline = QLabel("OBSERVATORY")
        tagline.setObjectName("brandTagline")
        brand_col.addWidget(tagline)
        brand_row.addLayout(brand_col, stretch=1)
        self.nav_collapse_btn = QPushButton("«")
        self.nav_collapse_btn.setObjectName("ghostButton")
        self.nav_collapse_btn.setFixedWidth(28)
        self.nav_collapse_btn.setToolTip("Collapse / expand navigation")
        self.nav_collapse_btn.clicked.connect(self._toggle_sidebar)
        brand_row.addWidget(self.nav_collapse_btn, alignment=Qt.AlignmentFlag.AlignTop)
        nav_layout.addLayout(brand_row)
        self.nav = QListWidget()
        self.nav.setObjectName("navList")
        self.nav.setAccessibleName("Primary navigation")
        self._nav_pages = list(PRIMARY_PAGES)
        self._nav_labels = [p.label for p in self._nav_pages]
        last_group = None
        for page in self._nav_pages:
            if page.group != last_group:
                hdr = QListWidgetItem(f"— {page.group} —")
                hdr.setFlags(Qt.ItemFlag.NoItemFlags)
                self.nav.addItem(hdr)
                last_group = page.group
            item = QListWidgetItem(page.label)
            item.setData(Qt.ItemDataRole.UserRole, page.id)
            item.setToolTip(page.tooltip or page.label)
            self.nav.addItem(item)
        # Restore last page or select first real page
        restored = False
        last_id = getattr(self.settings, "last_page_id", "observatory")
        for i in range(self.nav.count()):
            if self.nav.item(i).data(Qt.ItemDataRole.UserRole) == last_id:
                self.nav.setCurrentRow(i)
                restored = True
                break
        if not restored:
            for i in range(self.nav.count()):
                if self.nav.item(i).data(Qt.ItemDataRole.UserRole):
                    self.nav.setCurrentRow(i)
                    break
        self.nav.currentRowChanged.connect(self._on_nav)
        nav_layout.addWidget(self.nav, stretch=1)
        self.source_info = QLabel("No source loaded")
        self.source_info.setObjectName("navSourceInfo")
        self.source_info.setWordWrap(True)
        nav_layout.addWidget(self.source_info)
        self._nav_wrap = nav_wrap
        self._nav_splitter = splitter
        width = max(56, int(getattr(self.settings, "sidebar_width", 220) or 220))
        nav_wrap.setMinimumWidth(56)
        nav_wrap.setMaximumWidth(280)
        splitter.addWidget(nav_wrap)
        self._sidebar_collapsed = bool(getattr(self.settings, "sidebar_collapsed", False))
        if self._sidebar_collapsed:
            splitter.setSizes([56, 1200])
            self.nav_collapse_btn.setText("»")
            self._set_nav_collapsed_labels(True)
        else:
            nav_wrap.setMinimumWidth(180)
            splitter.setSizes([width, 1200])

        center_split = QSplitter()
        center_split.setOrientation(Qt.Orientation.Horizontal)

        self.tabs = QTabWidget()
        self.tabs.tabBar().hide()  # Single primary nav = sidebar; tabs are page stack only
        self.observatory = ObservatoryPanel()
        self.events = EventsPanel()
        self.quality = QualityPanel()
        self.provenance = ProvenancePanel()
        self.bot_library = BotLibraryPanel()
        self.compare = ComparePanel()
        self.classifier_compare = ClassifierComparePanel()
        self.workspace_panel = WorkspacePanel()
        self.annotations = AnnotationsPanel()
        self.export_panel = ExportPanel()
        self.history_panel = HistoryPanel()
        self.live_panel = LiveFeedPanel()

        self.global_observatory = GlobalObservatoryPanel()
        # Tab order MUST match PRIMARY_PAGES indices
        self.tabs.addTab(self.observatory, "Observatory")
        self.tabs.addTab(self.global_observatory, "Global")
        self.tabs.addTab(self.events, "Events")
        self.tabs.addTab(self.quality, "Dataset Health")
        self.tabs.addTab(self.provenance, "Provenance")
        self.tabs.addTab(self.bot_library, "Bot Library")

        compare_wrap = QWidget()
        compare_layout = QVBoxLayout(compare_wrap)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        compare_layout.addWidget(self.compare, stretch=3)
        compare_layout.addWidget(self.classifier_compare, stretch=2)
        self.tabs.addTab(compare_wrap, "Compare")

        self.tabs.addTab(self.workspace_panel, "Workspace")
        self.tabs.addTab(self.annotations, "Annotations")
        self.tabs.addTab(self.export_panel, "Exports")
        self.tabs.addTab(self.history_panel, "History")
        self.tabs.addTab(self.live_panel, "Live")

        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        self.tabs.addTab(self.settings_panel, "Settings")

        self.sources_panel = SourcesRegistryPanel()
        self.tabs.addTab(self.sources_panel, "Sources")

        assert self.tabs.count() == len(PRIMARY_PAGES), (
            f"Tab count {self.tabs.count()} != PRIMARY_PAGES {len(PRIMARY_PAGES)}"
        )
        center_split.addWidget(self.tabs)

        self.inspector = InspectorPanel()
        inspector_wrap = QWidget()
        i_layout = QVBoxLayout(inspector_wrap)
        i_layout.setContentsMargins(0, 0, 0, 0)
        i_layout.addWidget(self.inspector)
        inspector_wrap.setMinimumWidth(320)
        center_split.addWidget(inspector_wrap)
        center_split.setStretchFactor(0, 3)
        center_split.setStretchFactor(1, 2)

        splitter.addWidget(center_split)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(root)

        self.observatory.denominator_changed.connect(self._on_denominator)
        self.observatory.btn_open.clicked.connect(self.open_log)
        self.observatory.btn_demo.clicked.connect(self.load_demo)
        self.observatory.btn_global.clicked.connect(lambda: self._goto_page("global"))
        self.observatory.filter_requested.connect(self._on_composition_filter)
        self.observatory.actor_requested.connect(self._on_actor_selected)
        self.observatory.provenance_requested.connect(self._on_metric_provenance)
        self.observatory.clear_filters.connect(self._clear_all_filters)
        self.observatory.remove_filter.connect(self._remove_filter_chip)
        self.observatory.anomaly_time_requested.connect(self._on_anomaly_time)
        self.observatory.breakdown_row_requested.connect(self._on_breakdown_row)
        self.observatory.sources_requested.connect(lambda: self._goto_page("sources"))
        self.observatory.timeline_bucket_requested.connect(self._on_timeline_bucket)
        self.observatory.category_bar_requested.connect(self._on_category_bar)
        self.events.search.textChanged.connect(self._on_filter)
        self.events.category.currentIndexChanged.connect(self._on_filter)
        self.events.query_changed.connect(self._on_query)
        self.events.event_selected.connect(self._on_event_selected)
        self.history_panel.open_requested.connect(self._open_session_path)
        self.live_panel.start_requested.connect(self.start_live_tail)
        self.live_panel.start_pcap_file_requested.connect(self.open_pcap_file)
        self.live_panel.start_iface_requested.connect(self.start_live_iface)
        self.live_panel.stop_requested.connect(self.stop_live_tail)

        # Cold-start Source Fabric probe (deferred so the window can paint first)
        if getattr(self.settings, "auto_refresh_sources", True):
            from PySide6.QtCore import QTimer

            QTimer.singleShot(50, self._start_source_probe)

        # Apply restored page to tab stack
        self._goto_page(getattr(self.settings, "last_page_id", "observatory") or "observatory")

    def _build_status(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready")
        self.sensor_label = QLabel("Sensor ● IDLE")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(180)
        self.progress.setRange(0, 0)
        self.progress.hide()
        from botscope.gui.phase6_widgets import AnalysisStageStrip

        self.stage_strip = AnalysisStageStrip()
        status.addWidget(self.status_label, stretch=1)
        status.addWidget(self.stage_strip, stretch=1)
        status.addPermanentWidget(self.progress)
        status.addPermanentWidget(self.sensor_label)

    def _goto_nav(self, name: str) -> None:
        """Legacy label routing — prefer ``_goto_page``."""
        page_id = resolve_page_id(name)
        if page_id:
            self._goto_page(page_id)

    def _goto_page(self, page_id: str) -> None:
        """Authoritative navigation through PRIMARY_PAGES / tab stack."""
        try:
            idx = page_index(page_id)
        except KeyError:
            return
        changed = self.tabs.currentIndex() != idx
        self.tabs.setCurrentIndex(idx)
        # Sync sidebar selection (skip group headers)
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == page_id:
                self.nav.blockSignals(True)
                self.nav.setCurrentRow(i)
                self.nav.blockSignals(False)
                break
        if page_id == "global":
            self.global_observatory.ensure_loaded()
        if page_id == "sources":
            self.sources_panel.refresh()
        if changed:
            page = self.tabs.currentWidget()
            if page is not None:
                fade_in(page, duration_ms=180)
        # Persist last page locally
        if getattr(self.settings, "last_page_id", None) != page_id:
            self.settings.last_page_id = page_id
            from botscope.ux import save_settings

            save_settings(self.settings)

    def _on_composition_filter(self, family: str) -> None:
        """Click-through from KPI / ring → Events filtered by composition family."""
        self.session.filter_category = family
        self.events.category.blockSignals(True)
        # Prefer family key in search chip; clear exact category combo
        idx = self.events.category.findData(None)
        if idx >= 0:
            self.events.category.setCurrentIndex(idx)
        self.events.category.blockSignals(False)
        self.events.refresh(self.session)
        self.observatory.refresh(self.session)
        self._goto_page("events")
        self.status_label.setText(f"Filtered to {family.replace('_', ' ')} traffic")

    def _on_actor_selected(self, name: str) -> None:
        self.session.filter_text = name
        self.events.search.blockSignals(True)
        self.events.search.setText(name)
        self.events.search.blockSignals(False)
        self.events.refresh(self.session)
        self._goto_page("events")
        self.status_label.setText(f"Scoped to actor: {name}")

    def _on_metric_provenance(self, payload: object) -> None:
        if not isinstance(payload, dict):
            return
        lines = [
            "Why this number?",
            f"Metric: {payload.get('metric')}",
            f"Numerator: {payload.get('numerator'):,}"
            if isinstance(payload.get("numerator"), int)
            else f"Numerator: {payload.get('numerator')}",
            f"Denominator: {payload.get('denominator'):,} ({payload.get('denominator_label')})"
            if isinstance(payload.get("denominator"), int)
            else f"Denominator: {payload.get('denominator')}",
            f"Sources: {', '.join(payload.get('sources') or [])}",
            f"Filters: {', '.join(payload.get('filters') or ['(none)'])}",
            f"Time range: {payload.get('time_range')}",
            f"Classification version: {payload.get('ruleset_version')}",
            f"Demo data: {payload.get('is_demo')}",
        ]
        QMessageBox.information(self, "Statistic provenance", "\n".join(lines))
        self._goto_page("provenance")

    def _on_global_range(self) -> None:
        from datetime import datetime, timedelta, timezone

        key = self.range_combo.currentData()
        if key == "all" or key is None:
            self.session.time_range = TimeRange()
        else:
            hours = {"24h": 24, "7d": 24 * 7, "30d": 24 * 30}.get(str(key), 0)
            end = datetime.now(timezone.utc)
            start = end - timedelta(hours=hours)
            self.session.time_range = TimeRange(
                start=start.isoformat(),
                end=end.isoformat(),
            )
        self._refresh_all()
        self.status_label.setText(f"Time range: {self.range_combo.currentText()}")

    # ── dialogs ──────────────────────────────────────────────────────

    def show_welcome(self) -> None:
        dlg = WelcomeDialog(self)
        if dlg.exec() != WelcomeDialog.DialogCode.Accepted:
            return
        if dlg.action == WelcomeAction.OPEN_LOG:
            self.open_log()
        elif dlg.action == WelcomeAction.OPEN_SESSION:
            self.open_session()
        elif dlg.action == WelcomeAction.DEMO:
            self.load_demo()
        elif dlg.action == WelcomeAction.OPEN_RECENT and dlg.recent_path:
            self._open_recent_path(dlg.recent_path)
        elif dlg.action == WelcomeAction.GLOBAL:
            self._goto_nav("Global")

    def maybe_open_last_session(self) -> None:
        for entry in self.recents.existing():
            if entry.kind == "session":
                self._open_session_path(entry.path)
                return

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About BotScope",
            f"<h2>BotScope {__version__}</h2>"
            "<p><b>Automated traffic observatory</b> — Python-first, native desktop.</p>"
            "<p>Classify bots vs human-likely vs unknown on <i>your</i> server logs "
            "and PCAPs. No account. No required API keys.</p>"
            "<p>Measurements apply only to configured sensors/sources. "
            "Internet-wide figures are estimates only when methodology and data justify them.</p>"
            "<p>Network contribution defaults to <b>OFF</b>.</p>",
        )

    def show_methodology(self) -> None:
        QMessageBox.information(
            self,
            "Methodology",
            "BotScope estimates traffic classification from available evidence "
            "(user-agent signatures, published IP ranges, request patterns).\n\n"
            "It should not imply that every automated or human classification is certain.\n\n"
            "UNKNOWN is a valid scientific outcome.\n\n"
            "Shares use an explicit denominator (requests or bytes) and apply only "
            "to the loaded sensor/dataset — never the entire Internet.\n\n"
            "See Dataset Health and Provenance panels for coverage and exclusions.",
        )

    def show_glossary(self) -> None:
        from pathlib import Path

        from PySide6.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout

        dlg = QDialog(self)
        dlg.setWindowTitle("BotScope Glossary")
        dlg.resize(640, 520)
        layout = QVBoxLayout(dlg)
        body = QPlainTextEdit()
        body.setReadOnly(True)
        glossary = Path(__file__).resolve().parents[2] / "docs" / "GLOSSARY.md"
        if not glossary.exists():
            glossary = Path(__file__).resolve().parents[3] / "docs" / "GLOSSARY.md"
        try:
            text = glossary.read_text(encoding="utf-8")
        except OSError:
            text = (
                "Automated traffic — classified into automation categories.\n"
                "Human-likely — browser-like evidence.\n"
                "Unknown — unclassified; a valid scientific outcome.\n"
                "Request share / Byte share — percentages of the selected denominator.\n"
                "Confidence — classifier score; not certainty.\n"
                "Known bot — in Bot Library.\n"
                "Observed — seen in the current dataset.\n"
            )
        body.setPlainText(text)
        layout.addWidget(body)
        dlg.exec()

    def show_diagnostics(self) -> None:
        from botscope.sources.registry import REGISTRY
        from botscope.ux import settings_path

        lines = [
            f"BotScope {__version__}",
            f"Settings: {settings_path()}",
            f"Theme: {self.settings.theme}",
            f"Last page: {getattr(self.settings, 'last_page_id', '—')}",
            f"Registered sources: {len(REGISTRY)}",
            f"Dataset loaded: {self.session.loaded}",
            f"Demo: {self.session.is_demo}",
            f"Events: {len(self.session.events):,}",
            "Account required: No",
            "Cloud profile: No",
        ]
        board = getattr(self, "_source_health_board", None)
        if board is not None:
            lines.append(
                f"Source probe: {board.zero_auth_available}/{board.zero_auth_total} zero-auth"
            )
        text = "\n".join(lines)
        box = QMessageBox(self)
        box.setWindowTitle("Diagnostics")
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        copy = box.addButton("Copy Diagnostic Report", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        if box.clickedButton() is copy:
            from PySide6.QtGui import QGuiApplication

            QGuiApplication.clipboard().setText(text)

    def _toggle_sidebar(self) -> None:
        self._sidebar_collapsed = not getattr(self, "_sidebar_collapsed", False)
        if self._sidebar_collapsed:
            self._nav_wrap.setMinimumWidth(56)
            self._nav_splitter.setSizes([56, 1400])
            self.nav_collapse_btn.setText("»")
            self._set_nav_collapsed_labels(True)
        else:
            width = max(180, int(getattr(self.settings, "sidebar_width", 220) or 220))
            self._nav_wrap.setMinimumWidth(180)
            self._nav_splitter.setSizes([width, 1400])
            self.nav_collapse_btn.setText("«")
            self._set_nav_collapsed_labels(False)
        self.settings.sidebar_collapsed = self._sidebar_collapsed
        from botscope.ux import save_settings

        save_settings(self.settings)

    def _set_nav_collapsed_labels(self, collapsed: bool) -> None:
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            page_id = item.data(Qt.ItemDataRole.UserRole) if item else None
            if not page_id:
                item.setHidden(collapsed)
                continue
            page = next((p for p in PRIMARY_PAGES if p.id == page_id), None)
            if page is None:
                continue
            if collapsed:
                item.setText(page.label[:1].upper())
                item.setToolTip(page.label)
            else:
                item.setText(page.label)
                item.setToolTip(page.tooltip or page.label)

    def _start_source_probe(self) -> None:
        from botscope.gui.sources_panel import _ProbeWorker

        if getattr(self, "_source_probe", None) and self._source_probe.isRunning():
            return
        self._source_probe = _ProbeWorker(self)
        self._source_probe.finished_ok.connect(self._on_source_probe_done)
        self._source_probe.failed.connect(
            lambda msg: self.status_label.setText(f"Source probe: {msg}")
        )
        self._source_probe.start()

    def _on_source_probe_done(self, board) -> None:
        self._source_health_board = board
        ok = board.zero_auth_available
        total = board.zero_auth_total
        self.observatory.set_source_coverage(ok, total, active=0)
        self.status_label.setText(f"Sources ready: {ok}/{total} zero-auth available/cached")

    def _clear_all_filters(self) -> None:
        self.session.filter_category = None
        self.session.filter_text = ""
        self.session.query = ""
        self.events.search.blockSignals(True)
        self.events.search.clear()
        self.events.search.blockSignals(False)
        self.events.query.blockSignals(True)
        self.events.query.clear()
        self.events.query.blockSignals(False)
        idx = self.events.category.findData(None)
        if idx >= 0:
            self.events.category.blockSignals(True)
            self.events.category.setCurrentIndex(idx)
            self.events.category.blockSignals(False)
        self._refresh_all()

    def _remove_filter_chip(self, key: str) -> None:
        if key == "category":
            self.session.filter_category = None
            idx = self.events.category.findData(None)
            if idx >= 0:
                self.events.category.setCurrentIndex(idx)
        elif key == "text":
            self.session.filter_text = ""
            self.events.search.clear()
        elif key == "query":
            self.session.query = ""
            self.events.query.clear()
        elif key == "time":
            from botscope.workspace import TimeRange

            self.session.time_range = TimeRange()
            if hasattr(self, "range_combo"):
                self.range_combo.setCurrentIndex(0)
        self._refresh_all()

    def _on_anomaly_time(self, time_label: str) -> None:
        self.session.filter_text = ""
        # Scope Events via query on timestamp prefix when possible
        self.session.query = ""
        self.status_label.setText(f"Anomaly focus: {time_label} (open Events to inspect)")
        self._goto_page("events")

    def _on_breakdown_row(self, dimension: str, key: str) -> None:
        if dimension == "classification":
            self.session.filter_category = key
        else:
            self.session.filter_text = key
            self.events.search.blockSignals(True)
            self.events.search.setText(key)
            self.events.search.blockSignals(False)
        self._refresh_all()
        self._goto_page("events")

    def _on_timeline_bucket(self, label: str) -> None:
        self.session.filter_text = label
        self.events.search.blockSignals(True)
        self.events.search.setText(label)
        self.events.search.blockSignals(False)
        self._refresh_all()
        self._goto_page("events")
        self.status_label.setText(f"Timeline focus: {label}")

    def _on_category_bar(self, category: str) -> None:
        self.session.filter_category = category
        self._refresh_all()
        self._goto_page("events")
        self.status_label.setText(f"Category focus: {category}")

    # ── file / session ───────────────────────────────────────────────

    def open_log(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Web Log or PCAP",
            "",
            "Logs / Captures (*.log *.txt *.json *.jsonl *.ndjson *.pcap *.pcapng *.cap);;All files (*.*)",
        )
        if path:
            self._start_analyze(Path(path), is_demo=False)

    def open_pcap_file(self, path: str) -> None:
        self._start_analyze(Path(path), is_demo=False)
        self.status_label.setText(f"Analyzing authorized PCAP {path}")

    def open_session(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open BotScope Session (.bscope folder)")
        if path:
            self._open_session_path(path)

    def _open_session_path(self, path: str) -> None:
        try:
            loaded = load_analysis_session(path, remember=True)
        except Exception as exc:
            QMessageBox.critical(self, "Failed to open session", str(exc))
            return
        self.session.source_path = Path(loaded.meta.source_path) if loaded.meta and loaded.meta.source_path else Path(path)
        self.session.session_path = loaded.path
        self.session.session_id = loaded.session_id
        self.session.is_demo = loaded.result.is_demo
        self.session.result = loaded.result
        self.session.apply_workspace(loaded.workspace)
        self.session.selected_event_id = None
        self._refresh_all()
        self.status_label.setText(f"Opened session {path}")
        self.sensor_label.setText("Sensor ● SESSION")
        self._remember_path(path, kind="session")
        self.history_panel.reload()

    def save_session(self) -> None:
        if self.session.session_path:
            self._persist_to(self.session.session_path)
        else:
            self.save_session_as()

    def save_session_as(self) -> None:
        if not self.session.loaded:
            QMessageBox.information(self, "Save Session", "Nothing to save — load an analysis first.")
            return
        suggested = suggest_session_name(self.session.source_path, is_demo=self.session.is_demo)
        path = QFileDialog.getExistingDirectory(
            self,
            "Save Session As (.bscope folder parent)",
        )
        if not path:
            return
        target = Path(path) / suggested
        self._persist_to(target)

    def _persist_to(self, target: Path) -> None:
        if not self.session.loaded or self.session.result is None:
            QMessageBox.information(self, "Save Session", "Nothing to save.")
            return
        try:
            loaded = save_analysis_session(
                target,
                self.session.events,
                source_path=self.session.source_path,
                is_demo=self.session.is_demo,
                workspace=self.session.to_workspace(),
                remember=True,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self.session.session_path = loaded.path
        self.session.session_id = loaded.session_id
        self.session.result = loaded.result
        self.status_label.setText(f"Saved session {loaded.path}")
        self._remember_path(loaded.path, kind="session")
        self.history_panel.reload()
        self.annotations.refresh(self.session)
        self.workspace_panel.refresh(self.session)

    def load_demo(self) -> None:
        path = ensure_demo_log()
        self.status_label.setText(DEMO_NOTICE)
        self._start_analyze(path, is_demo=True)

    def _start_analyze(self, path: Path, *, is_demo: bool) -> None:
        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "Busy", "Analysis already running.")
            return
        self.progress.show()
        if hasattr(self, "stage_strip"):
            self.stage_strip.set_stage_message("Reading dataset")
        self.sensor_label.setText("Sensor ● ANALYZING")
        self.status_label.setText(f"Analyzing {path.name}…")
        self._worker = AnalyzeWorker(
            path,
            is_demo=is_demo,
            privacy=self._privacy_config(),
            parent=self,
        )
        self._worker.progress.connect(self._on_analyze_progress)
        self._worker.finished_ok.connect(
            lambda result: self._on_analyze_done(path, result, is_demo)
        )
        self._worker.failed.connect(self._on_analyze_failed)
        self._worker.start()

    def _on_analyze_progress(self, message: str) -> None:
        self.status_label.setText(message)
        if hasattr(self, "stage_strip"):
            self.stage_strip.set_stage_message(message)

    def _on_analyze_done(self, path: Path, result: AnalysisResult, is_demo: bool) -> None:
        self.progress.hide()
        if hasattr(self, "stage_strip"):
            self.stage_strip.clear()
        self.session.source_path = path
        self.session.is_demo = is_demo
        self.session.result = result
        self.session.session_path = result.session_path
        self.session.session_id = result.session_id
        self.session.selected_event_id = None
        self.session.live_mode = False
        self._refresh_all()
        self.sensor_label.setText("Sensor ● LOADED" + (" · DEMO" if is_demo else ""))
        self.status_label.setText(
            f"Loaded {len(result.events):,} events from {path.name}"
            + (" [DEMO DATA]" if is_demo else "")
        )
        if not is_demo:
            self._remember_path(path)

    def _on_analyze_failed(self, message: str) -> None:
        self.progress.hide()
        if hasattr(self, "stage_strip"):
            self.stage_strip.clear()
        self.sensor_label.setText("Sensor ● ERROR")
        self.status_label.setText("Analysis failed")
        # Prefer actionable message; keep technical details expandable
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("Dataset could not be analyzed")
        box.setText("Dataset could not be analyzed.")
        box.setInformativeText(f"Reason:\n{message}")
        box.setDetailedText(message)
        box.exec()

    # ── live feed ────────────────────────────────────────────────────

    def _ensure_live_infra(self, source_label: str):
        from botscope.live import (
            AlertEngine,
            FanInAggregator,
            LiveSessionWriter,
            default_alert_rules,
            suggest_live_session_path,
        )

        if self._fanin is None:
            self._fanin = FanInAggregator(max_hz=5.0)
        if self._alert_engine is None:
            self._alert_engine = AlertEngine(rules=default_alert_rules())
        if self._live_writer is None:
            path = suggest_live_session_path(
                Path(self.session.session_path).parent
                if self.session.session_path
                else Path.cwd()
            )
            self._live_writer = LiveSessionWriter(
                path,
                source_label=source_label,
                max_memory_events=50_000,
            )
            sid = self._live_writer.open(config={"gui": True})
            self.session.session_path = self._live_writer.path
            self.session.session_id = sid
        return self._fanin

    def start_live_tail(self, path: str) -> None:
        fanin = self._ensure_live_infra(str(path))
        worker = LiveLogTailWorker(
            Path(path),
            sensor_id=f"log:{Path(path).name}",
            privacy=self._privacy_config(),
            fanin=fanin,
            parent=self,
        )
        worker.snapshot_ready.connect(self._on_live_snapshot)
        worker.events_batch.connect(self._on_live_events)
        worker.status.connect(self.live_panel.set_status_text)
        worker.failed.connect(self._on_live_failed)
        self._live_workers.append(worker)
        self.session.live_mode = True
        self.session.source_path = Path(path)
        self.sensor_label.setText("Sensor ● LIVE")
        self.status_label.setText(f"Authorized live tail: {path}")
        self._remember_path(path, kind="log")
        worker.start()

    def start_live_iface(self, interface: str, bpf: str) -> None:
        fanin = self._ensure_live_infra(f"live:{interface}")
        worker = LivePacketCaptureWorker(
            interface,
            bpf_filter=bpf or None,
            privacy=self._privacy_config(),
            fanin=fanin,
            parent=self,
        )
        worker.snapshot_ready.connect(self._on_live_snapshot)
        worker.events_batch.connect(self._on_live_events)
        worker.status.connect(self.live_panel.set_status_text)
        worker.failed.connect(self._on_live_failed)
        self._live_workers.append(worker)
        self.session.live_mode = True
        self.session.source_path = Path(f"live:{interface}")
        self.sensor_label.setText("Sensor ● LIVE")
        self.status_label.setText(f"Authorized live capture: {interface}")
        worker.start()

    def stop_live_tail(self) -> None:
        for worker in list(self._live_workers):
            if worker.isRunning():
                worker.request_stop()
                worker.wait(3000)
        self._live_workers.clear()
        if self._live_writer is not None:
            root = self._live_writer.close()
            if root is not None:
                self.status_label.setText(f"Live session saved: {root}")
            self._live_writer = None
        self._fanin = None
        self._alert_engine = None
        self.session.live_mode = False
        self.sensor_label.setText("Sensor ● IDLE")
        self.live_panel.set_status_text("Idle — not live.")

    def _on_live_snapshot(self, snap: ObservatorySnapshot) -> None:
        self.observatory.apply_snapshot(snap)
        if self._live_writer is not None:
            self._live_writer.note_snapshot(snap)
        if self._alert_engine is not None:
            alerts = self._alert_engine.evaluate(snap)
            if alerts:
                self.live_panel.append_alerts(alerts)
                self.status_label.setText(alerts[-1].message)
        if snap.is_live:
            self.sensor_label.setText(
                f"Sensor ● LIVE  ·  {snap.events_per_second:.2f} evt/s"
            )
        self.status_label.setText(
            f"Live snapshot: {snap.total_events:,} events @ {snap.events_per_second:.2f} evt/s"
        )

    def _on_live_events(self, batch) -> None:
        if self._live_writer is not None:
            self._live_writer.append(batch)
            existing = self._live_writer.memory_events
        else:
            existing = list(self.session.events)
            existing.extend(batch)
            if len(existing) > 50_000:
                existing = existing[-50_000:]
        stats = aggregate_events(existing, is_demo=False)
        self.session.result = AnalysisResult(events=existing, stats=stats, is_demo=False)
        self.session.is_demo = False
        self.events.refresh(self.session)

    def _on_live_failed(self, message: str) -> None:
        self.session.live_mode = False
        self.sensor_label.setText("Sensor ● ERROR")
        QMessageBox.critical(self, "Live feed failed", message)

    # ── refresh / filters ────────────────────────────────────────────

    def _set_empty_state(self) -> None:
        self.inspector.clear()
        self.observatory.refresh(self.session)

    def _refresh_all(self) -> None:
        src = str(self.session.source_path) if self.session.source_path else "—"
        demo = "\nDEMO DATA" if self.session.is_demo else ""
        sess = f"\nSession: {self.session.session_path}" if self.session.session_path else ""
        self.source_info.setText(f"Source:\n{src}{demo}{sess}")
        self.observatory.denominator.blockSignals(True)
        self.observatory.denominator.setCurrentText(self.session.denominator)
        self.observatory.denominator.blockSignals(False)
        self.observatory.refresh(self.session)
        self.events.refresh(self.session)
        self.quality.refresh(self.session)
        self.provenance.refresh(self.session)
        self.bot_library.mark_observed(self.session)
        self.inspector.show_event(self.session)
        self.classifier_compare.refresh(self.session)
        self.workspace_panel.refresh(self.session)
        self.annotations.refresh(self.session)
        self.export_panel.refresh(self.session)
        if hasattr(self.compare, "refresh"):
            self.compare.refresh(self.session)

        events_n = len(self.session.events)
        range_txt = self.range_combo.currentText() if hasattr(self, "range_combo") else "Entire dataset"
        demo_flag = "  ·  DEMO DATA" if self.session.is_demo else ""
        analysis = "Complete" if self.session.loaded else "Idle"
        self.status_label.setText(
            f"Dataset: {src}  ·  Events: {events_n:,}  ·  Range: {range_txt}  ·  "
            f"Analysis: {analysis}{demo_flag}"
        )

    def _on_nav(self, row: int) -> None:
        item = self.nav.item(row)
        if item is None:
            return
        page_id = item.data(Qt.ItemDataRole.UserRole)
        if not page_id:
            return  # group header
        try:
            idx = page_index(str(page_id))
        except KeyError:
            return
        self.tabs.setCurrentIndex(idx)
        if page_id == "global":
            self.global_observatory.ensure_loaded()
        if page_id == "sources":
            self.sources_panel.refresh()

    def _on_denominator(self, value: str) -> None:
        self.session.denominator = value
        self.observatory.refresh(self.session)
        self.provenance.refresh(self.session)
        self.workspace_panel.refresh(self.session)

    def _on_filter(self) -> None:
        self.session.filter_text = self.events.search.text()
        self.session.filter_category = self.events.category.currentData()
        self.events.refresh(self.session)
        self.observatory.refresh(self.session)
        self.workspace_panel.refresh(self.session)

    def _on_query(self) -> None:
        text = self.events.query.text().strip()
        self.session.query = text
        if text:
            try:
                self.session.query_predicates()
            except QueryError as exc:
                QMessageBox.warning(self, "Invalid query", str(exc))
                return
        self.events.refresh(self.session)
        self.workspace_panel.refresh(self.session)

    def _on_event_selected(self, event_id: str) -> None:
        self.session.selected_event_id = event_id
        self.inspector.show_event(self.session)
        self.provenance.refresh(self.session)

    # ── ease of access ───────────────────────────────────────────────

    def _privacy_config(self) -> PrivacyConfig:
        return PrivacyConfig(
            hash_ips=self.settings.hash_ips,
            truncate_ips=self.settings.truncate_ips,
            redact_query=self.settings.redact_query,
        )

    def _remember_path(self, path: str | Path, *, kind: str | None = None) -> None:
        resolved_kind = kind or classify_path(path)
        if resolved_kind not in {"log", "pcap", "session", "other"}:
            resolved_kind = "other"
        self.recents.remember(path, kind=resolved_kind)  # type: ignore[arg-type]
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        if not hasattr(self, "_recent_menu"):
            return
        self._recent_menu.clear()
        entries = self.recents.existing()
        if not entries:
            empty = QAction("(no recent files)", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
            return
        for entry in entries[:12]:
            label = entry.label or Path(entry.path).name
            act = QAction(f"{label}  ·  {entry.kind}", self)
            act.setToolTip(entry.path)
            act.triggered.connect(
                lambda _checked=False, p=entry.path: self._open_recent_path(p)
            )
            self._recent_menu.addAction(act)
        self._recent_menu.addSeparator()
        clear = QAction("Clear Recent List", self)
        clear.triggered.connect(self._clear_recents)
        self._recent_menu.addAction(clear)

    def _clear_recents(self) -> None:
        self.recents.entries = []
        self.recents.save()
        self._rebuild_recent_menu()

    def _open_recent_path(self, path: str) -> None:
        target = Path(path)
        if not target.exists():
            QMessageBox.warning(self, "Missing file", f"No longer found:\n{path}")
            self.recents.load()
            self._rebuild_recent_menu()
            return
        if classify_path(target) == "session":
            self._open_session_path(str(target))
        else:
            self._start_analyze(target, is_demo=False)

    def quick_export_markdown(self) -> None:
        if not self.session.loaded or self.session.result is None:
            QMessageBox.information(self, "Export", "Load an analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Quick Export Markdown",
            "botscope_report.md",
            "Markdown (*.md);;All files (*.*)",
        )
        if not path:
            return
        from botscope.reports import build_report, export_markdown

        report = build_report(
            self.session.result.stats,
            events=self.session.events,
            is_demo=self.session.is_demo,
        )
        export_markdown(report, path)
        self.status_label.setText(f"Exported Markdown → {path}")

    def _on_settings_changed(self, settings: AppSettings) -> None:
        self.settings = settings
        self.session.denominator = settings.default_denominator
        set_reduce_motion(getattr(settings, "reduce_motion", False))
        set_chart_theme(settings.theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet_for(settings.theme))
        # Repaint charts for new palette
        self.observatory.timeline.update()
        self.observatory.categories.update()
        if self.session.loaded:
            self.observatory.denominator.blockSignals(True)
            self.observatory.denominator.setCurrentText(settings.default_denominator)
            self.observatory.denominator.blockSignals(False)
            self._on_denominator(settings.default_denominator)
        self.status_label.setText("Settings applied (local only)")
        fade_in(self.settings_panel, duration_ms=160)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        local = urls[0].toLocalFile()
        if not local:
            return
        path = Path(local)
        if classify_path(path) == "session" or (
            path.is_dir() and (path / "events.jsonl").exists()
        ):
            self._open_session_path(str(path))
        elif path.is_file():
            self._start_analyze(path, is_demo=False)
        else:
            QMessageBox.information(
                self,
                "Drop",
                "Drop a web log, PCAP, or .bscope session folder.",
            )

    def closeEvent(self, event) -> None:
        self.stop_live_tail()
        try:
            sizes = self._nav_splitter.sizes()
            if sizes and sizes[0] >= 120:
                self.settings.sidebar_width = sizes[0]
            self.settings.sidebar_collapsed = getattr(self, "_sidebar_collapsed", False)
            from botscope.ux import save_settings

            save_settings(self.settings)
        except Exception:
            pass
        super().closeEvent(event)
