"""Phase 5 Observatory dashboard widgets — ring, actors, pulse, KPI."""

from __future__ import annotations

from PySide6.QtCore import Property, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from botscope.gui.dashboard_stats import ActorShare, CompositionShare, TrafficPulse
from botscope.gui.motion import animate_float, pulse_opacity, reduce_motion
from botscope.gui.theme import chart_colors
from botscope.gui.widgets import fmt_int, fmt_pct


class KpiCard(QFrame):
    """Prominent share card with percentage + absolute count + tooltip."""

    clicked = Signal(str)

    def __init__(
        self,
        key: str,
        title: str,
        *,
        tooltip: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.key = key
        self.setObjectName("metricTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        self.caption = QLabel(title.upper())
        self.caption.setObjectName("metricCaption")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.detail = QLabel("")
        self.detail.setObjectName("muted")
        self.badge = QLabel("")
        self.badge.setObjectName("provenanceBadge")
        layout.addWidget(self.caption)
        layout.addWidget(self.value)
        layout.addWidget(self.detail)
        layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignLeft)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._last_pct: float | None = None

    def set_share(self, pct: float | None, count: int, *, provenance: str = "CLASSIFIED") -> None:
        changed = pct != self._last_pct and self._last_pct is not None
        self._last_pct = pct
        self.value.setText(fmt_pct(pct) if pct is not None else "—")
        self.detail.setText(f"{fmt_int(count)} events")
        self.badge.setText(provenance)
        if changed:
            pulse_opacity(self.value, duration_ms=160)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.key)
        super().mousePressEvent(event)


class ShareRing(QWidget):
    """Circular composition ring (automated / human / unknown)."""

    segment_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._auto = 0.0
        self._human = 0.0
        self._unknown = 0.0
        self._progress = 1.0
        self._center_label = "AUTOMATED"
        self._center_value = "—"
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip("Click a segment to filter events by classification family")

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, float(value)))
        self.update()

    progress = Property(float, _get_progress, _set_progress)

    def set_composition(self, comp: CompositionShare | None) -> None:
        if comp is None or comp.total <= 0:
            self._auto = self._human = self._unknown = 0.0
            self._center_value = "—"
            self._progress = 1.0
        else:
            self._auto = comp.automated
            self._human = comp.human_likely
            self._unknown = comp.unknown
            self._center_value = fmt_pct(comp.automated)
            self._center_label = "AUTOMATED"
            if reduce_motion():
                self._progress = 1.0
            else:
                animate_float(self, b"progress", 1.0, start=0.0, duration_ms=480)
        self.update()

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(colors.get("paper", "#eef3f7")))
        grad.setColorAt(1.0, QColor(colors.get("paper_deep", colors["paper"])))
        painter.fillRect(self.rect(), grad)

        side = min(self.width(), self.height()) - 16
        x = (self.width() - side) // 2
        y = (self.height() - side) // 2
        rect = self.rect().adjusted(
            x + 8, y + 8, -(self.width() - x - side) + 8, -(self.height() - y - side) + 8
        )

        total = self._auto + self._human + self._unknown
        if total <= 0:
            painter.setPen(QColor(colors["muted"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No composition data")
            painter.end()
            return

        # Track ring
        track = QPen(QColor(colors["grid"]))
        track.setWidth(28)
        track.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(track)
        painter.drawArc(rect.adjusted(20, 20, -20, -20), 0, 360 * 16)

        start = 90 * 16
        segments = [
            ("automated", self._auto, colors["auto"]),
            ("human_likely", self._human, colors["human"]),
            ("unknown", self._unknown, colors["total"]),
        ]
        pen = QPen()
        pen.setWidth(28)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p = self._progress
        for _key, share, color in segments:
            span = int(-360 * 16 * (share / total) * p)
            pen.setColor(QColor(color))
            painter.setPen(pen)
            painter.drawArc(rect.adjusted(20, 20, -20, -20), start, span)
            start += span

        painter.setPen(QColor(colors["muted"]))
        caption_font = QFont(painter.font())
        caption_font.setPointSize(9)
        caption_font.setBold(True)
        caption_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        painter.setFont(caption_font)
        painter.drawText(
            rect.adjusted(0, -22, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            self._center_label,
        )
        painter.setPen(QColor(colors["ink"]))
        value_font = QFont(painter.font())
        value_font.setFamily("Cascadia Mono")
        value_font.setPointSize(20)
        value_font.setBold(True)
        painter.setFont(value_font)
        painter.drawText(
            rect.adjusted(0, 14, 0, 0),
            Qt.AlignmentFlag.AlignCenter,
            self._center_value,
        )
        painter.end()

    def mousePressEvent(self, event) -> None:
        cx, cy = self.width() / 2, self.height() / 2
        dx, dy = event.position().x() - cx, event.position().y() - cy
        if abs(dx) > abs(dy):
            self.segment_clicked.emit("automated" if dx < 0 else "human_likely")
        else:
            self.segment_clicked.emit("unknown" if dy > 0 else "automated")
        super().mousePressEvent(event)


class TopActorsPanel(QWidget):
    actor_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Top Automated Actors")
        title.setObjectName("sectionTitle")
        outer.addWidget(title)
        note = QLabel("Shares are % of automated traffic in the current view (evidence-backed).")
        note.setObjectName("muted")
        note.setWordWrap(True)
        outer.addWidget(note)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._on_item)
        outer.addWidget(self.list)

    def set_actors(self, actors: list[ActorShare]) -> None:
        self.list.clear()
        if not actors:
            item = QListWidgetItem("No automated traffic observed in this view.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(item)
            return
        for actor in actors:
            text = f"{actor.name:<28} {actor.share * 100:5.1f}%   ({actor.count:,})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, actor.name)
            item.setToolTip(f"{actor.category or '—'} · {actor.count:,} events")
            self.list.addItem(item)

    def _on_item(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.ItemDataRole.UserRole)
        if name:
            self.actor_selected.emit(str(name))


class ConfidencePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Classification Confidence")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.body = QLabel("Load a dataset to see confidence distribution.")
        self.body.setObjectName("muted")
        self.body.setWordWrap(True)
        layout.addWidget(self.body)

    def set_buckets(self, buckets: list[tuple[str, int]]) -> None:
        total = sum(n for _, n in buckets) or 1
        lines = []
        for name, n in buckets:
            bar = "█" * max(0, int(20 * n / total))
            lines.append(f"{name:<12} {bar} {n:,} ({100 * n / total:.0f}%)")
        self.body.setText("\n".join(lines) if buckets else "No confidence data.")
        self.body.setObjectName("")


class TrafficPulsePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Traffic Pulse")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        self.body.setMaximumHeight(180)
        self.body.setPlaceholderText("Pulse appears after analysis…")
        layout.addWidget(self.body)

    def set_pulse(self, pulse: TrafficPulse | None) -> None:
        if pulse is None:
            self.body.setPlainText("No dataset loaded.")
            return
        self.body.setPlainText("\n".join(pulse.summary_lines))


class ExplainPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sectionPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        row = QHBoxLayout()
        title = QLabel("Explain this view")
        title.setObjectName("sectionTitle")
        row.addWidget(title)
        row.addStretch()
        self.why_btn = QPushButton("Why this number?")
        self.why_btn.setObjectName("ghostButton")
        row.addWidget(self.why_btn)
        layout.addLayout(row)
        self.body = QPlainTextEdit()
        self.body.setReadOnly(True)
        self.body.setMaximumHeight(140)
        layout.addWidget(self.body)

    def set_text(self, text: str) -> None:
        self.body.setPlainText(text)
