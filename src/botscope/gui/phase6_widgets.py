"""Phase 6 dashboard widgets — anomalies, breakdown, filter chips, stages."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from botscope.gui.anomaly import AnomalyFinding
from botscope.gui.breakdown import BreakdownRow


class FilterChipBar(QWidget):
    """Interactive removable filter chips + clear-all."""

    clear_all = Signal()
    chip_removed = Signal(str)  # key

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self.caption = QLabel("Filters:")
        self.caption.setObjectName("muted")
        self._layout.addWidget(self.caption)
        self._chips_host = QHBoxLayout()
        self._layout.addLayout(self._chips_host)
        self._layout.addStretch()
        self.clear_btn = QPushButton("Clear all")
        self.clear_btn.setObjectName("ghostButton")
        self.clear_btn.clicked.connect(self.clear_all.emit)
        self.clear_btn.hide()
        self._layout.addWidget(self.clear_btn)
        self.hide()

    def set_chips(self, chips: list[tuple[str, str]]) -> None:
        """chips: list of (key, label)."""
        while self._chips_host.count():
            item = self._chips_host.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if not chips:
            self.clear_btn.hide()
            self.hide()
            return
        for key, label in chips:
            btn = QToolButton()
            btn.setText(f"{label}  ×")
            btn.setObjectName("ghostButton")
            btn.setToolTip(f"Remove filter: {label}")
            btn.clicked.connect(lambda checked=False, k=key: self.chip_removed.emit(k))
            self._chips_host.addWidget(btn)
        self.clear_btn.show()
        self.show()


class AnomalyPanel(QWidget):
    anomaly_selected = Signal(str)  # time_label

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Anomalies")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        note = QLabel(
            "Statistical deviations within this dataset. "
            "Not malice labels — investigate, do not assume attack."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._on_item)
        layout.addWidget(self.list)

    def set_findings(self, findings: list[AnomalyFinding]) -> None:
        self.list.clear()
        if not findings:
            item = QListWidgetItem("No anomalies detected for the current view.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(item)
            return
        for f in findings:
            text = (
                f"[{f.severity.upper()}] {f.time_label}  ·  {f.metric}\n"
                f"  baseline={f.baseline}  observed={f.observed}\n"
                f"  {f.reason}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, f.time_label)
            item.setToolTip(f.related or f.reason)
            self.list.addItem(item)

    def _on_item(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        if key:
            self.anomaly_selected.emit(str(key))


class BreakdownExplorer(QWidget):
    row_selected = Signal(str, str)  # dimension, key

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        header = QHBoxLayout()
        title = QLabel("Traffic Breakdown")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Dimension:"))
        self.dimension = QComboBox()
        self.dimension.currentTextChanged.connect(self._emit_dim_change)
        header.addWidget(self.dimension)
        layout.addLayout(header)
        self.crumb = QLabel("")
        self.crumb.setObjectName("muted")
        layout.addWidget(self.crumb)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._on_item)
        layout.addWidget(self.list)
        self._on_dim = None

    def _emit_dim_change(self, text: str) -> None:
        if hasattr(self, "_on_dim") and callable(self._on_dim):
            self._on_dim(text)

    def set_dimension_handler(self, cb) -> None:
        self._on_dim = cb

    def set_dimensions(self, dims: list[str], current: str | None = None) -> None:
        self.dimension.blockSignals(True)
        self.dimension.clear()
        for d in dims:
            self.dimension.addItem(d)
        if current and current in dims:
            self.dimension.setCurrentText(current)
        self.dimension.blockSignals(False)

    def set_rows(self, rows: list[BreakdownRow], *, crumb: str = "") -> None:
        self.crumb.setText(crumb)
        self.list.clear()
        if not rows:
            item = QListWidgetItem("No matching traffic for this breakdown.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(item)
            return
        for row in rows:
            text = f"{row.key:<40} {row.share * 100:5.1f}%  ({row.count:,})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, row.key)
            item.setToolTip(f"{row.count:,} events · {row.bytes_out:,} bytes")
            self.list.addItem(item)

    def current_dimension(self) -> str:
        return self.dimension.currentText() or "classification"

    def _on_item(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        if key:
            self.row_selected.emit(self.current_dimension(), str(key))


class AnalysisStageStrip(QWidget):
    """Labeled analysis stages — determinate only when progress is known."""

    STAGES = (
        "Reading dataset",
        "Normalizing records",
        "Classifying traffic",
        "Resolving identities",
        "Calculating statistics",
        "Building timeline",
        "Validating provenance",
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        self.label = QLabel("")
        self.label.setObjectName("muted")
        layout.addWidget(self.label)
        self.hide()

    def set_stage_message(self, message: str) -> None:
        msg = (message or "").strip()
        if not msg:
            self.hide()
            return
        # Map free-form worker messages onto nearest stage label when possible
        lower = msg.lower()
        stage = None
        for s in self.STAGES:
            if s.split()[0].lower() in lower or any(
                w.lower() in lower for w in s.split() if len(w) > 4
            ):
                stage = s
                break
        if stage:
            self.label.setText(f"Analysis · {stage} — {msg}")
        else:
            self.label.setText(f"Analysis · {msg}")
        self.show()

    def clear(self) -> None:
        self.label.setText("")
        self.hide()


def install_stat_copy_menu(
    widget: QWidget,
    *,
    value_fn,
    context_fn,
    provenance_fn=None,
) -> None:
    """Right-click: Copy value / Copy with context / Copy provenance."""

    widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _menu(pos) -> None:
        menu = QMenu(widget)
        act_val = QAction("Copy value", widget)
        act_ctx = QAction("Copy with context", widget)
        act_prov = QAction("Copy provenance", widget)
        menu.addAction(act_val)
        menu.addAction(act_ctx)
        if provenance_fn:
            menu.addAction(act_prov)

        def copy_val() -> None:
            QGuiApplication.clipboard().setText(str(value_fn() or ""))

        def copy_ctx() -> None:
            QGuiApplication.clipboard().setText(str(context_fn() or ""))

        def copy_prov() -> None:
            if provenance_fn:
                QGuiApplication.clipboard().setText(str(provenance_fn() or ""))

        act_val.triggered.connect(copy_val)
        act_ctx.triggered.connect(copy_ctx)
        act_prov.triggered.connect(copy_prov)
        menu.exec(widget.mapToGlobal(pos))

    widget.customContextMenuRequested.connect(_menu)
