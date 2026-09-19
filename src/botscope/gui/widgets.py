"""Reusable Observatory widgets (native Qt — not web components)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from botscope.gui.motion import pulse_opacity
from botscope.gui.theme import chart_colors


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def fmt_int(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,}"


def fill_paper(painter: QPainter, rect) -> None:
    """Subtle vertical paper wash used by painted charts."""
    colors = chart_colors()
    grad = QLinearGradient(0, 0, 0, rect.height())
    grad.setColorAt(0.0, QColor(colors.get("paper", "#eef3f7")))
    grad.setColorAt(1.0, QColor(colors.get("paper_deep", colors["paper"])))
    painter.fillRect(rect, grad)


class ProvenanceBadge(QLabel):
    def __init__(self, level: str = "OBSERVED", parent=None) -> None:
        super().__init__(level, parent)
        self.setObjectName("provenanceBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class MetricTile(QFrame):
    def __init__(
        self,
        caption: str,
        value: str = "—",
        provenance: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.caption = QLabel(caption.upper())
        self.caption.setObjectName("metricCaption")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValue")
        layout.addWidget(self.caption)
        layout.addWidget(self.value_label)
        self.badge = ProvenanceBadge(provenance or "")
        if provenance:
            layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.badge.hide()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._last_value = value

    def set_value(self, value: str, provenance: str | None = None) -> None:
        changed = value != self._last_value and self._last_value != "—"
        self._last_value = value
        self.value_label.setText(value)
        if provenance:
            self.badge.setText(provenance)
            self.badge.show()
        if changed:
            pulse_opacity(self.value_label, duration_ms=160)


class BrandMark(QWidget):
    """Compact radar-scope mark for welcome / about chrome."""

    def __init__(self, *, size: int = 72, parent=None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self._size / 2
        r = self._size * 0.42
        painter.setBrush(QColor(colors["ink"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(colors["grid"]), 1.5))
        painter.drawEllipse(int(cx - r * 0.88), int(cy - r * 0.88), int(1.76 * r), int(1.76 * r))
        painter.setPen(QPen(QColor(colors.get("accent", colors["auto"])), 2))
        painter.drawEllipse(int(cx - r * 0.55), int(cy - r * 0.55), int(1.1 * r), int(1.1 * r))
        painter.setPen(QPen(QColor(colors.get("accent_bright", colors["auto"])), 2.5))
        painter.drawLine(int(cx), int(cy), int(cx), int(cy - r * 0.88))
        painter.setBrush(QColor(colors.get("accent_bright", colors["auto"])))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(cx - 3), int(cy - 3), 6, 6)
        painter.end()


class TimelineChart(QWidget):
    """Native painted timeline — click a bar to focus that bucket."""

    bucket_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._series: list[tuple[str, int, int, int]] = []
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click a time bar to filter Events to that interval")

    def set_series(self, series: list[tuple[str, int, int, int]]) -> None:
        self._series = list(series)
        self.update()

    def _bar_geometry(self):
        rect = self.rect().adjusted(40, 16, -12, -28)
        n = max(len(self._series), 1)
        gap = 2
        bar_w = max(2, (rect.width() - gap * max(0, n - 1)) / n)
        return rect, bar_w, gap

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect, bar_w, gap = self._bar_geometry()
        fill_paper(painter, self.rect())
        painter.setPen(QPen(QColor(colors["grid"])))
        painter.drawRect(rect)

        if not self._series:
            painter.setPen(QColor(colors["muted"]))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No timeline data loaded")
            painter.end()
            return

        max_total = max(row[1] for row in self._series) or 1
        n = len(self._series)

        for i, (label, total, auto, human) in enumerate(self._series):
            x = rect.left() + i * (bar_w + gap)
            h_total = (total / max_total) * rect.height()
            h_auto = (auto / max_total) * rect.height()
            h_human = (human / max_total) * rect.height()
            y_base = rect.bottom()

            painter.fillRect(
                int(x),
                int(y_base - h_total),
                max(1, int(bar_w)),
                int(h_total),
                QColor(colors["total"]),
            )
            painter.fillRect(
                int(x),
                int(y_base - h_auto),
                max(1, int(bar_w)),
                int(h_auto),
                QColor(colors["auto"]),
            )
            if h_human > 0:
                painter.fillRect(
                    int(x),
                    int(y_base - h_total),
                    max(1, int(bar_w)),
                    int(min(h_human, h_total)),
                    QColor(colors["human"]),
                )

            if n <= 24 or i % max(1, n // 12) == 0:
                painter.setPen(QColor(colors["muted"]))
                painter.drawText(
                    int(x),
                    rect.bottom() + 4,
                    int(bar_w) + 20,
                    20,
                    Qt.AlignmentFlag.AlignLeft,
                    label[-5:] if len(label) > 5 else label,
                )

        painter.setPen(QColor(colors["ink"]))
        painter.fillRect(rect.left(), 4, 10, 10, QColor(colors["auto"]))
        painter.drawText(rect.left() + 14, 13, "automated")
        painter.fillRect(rect.left() + 100, 4, 10, 10, QColor(colors["human"]))
        painter.drawText(rect.left() + 114, 13, "human-likely peak")
        painter.fillRect(rect.left() + 250, 4, 10, 10, QColor(colors["total"]))
        painter.drawText(rect.left() + 264, 13, "total · click a bar to inspect")
        painter.end()

    def mousePressEvent(self, event) -> None:
        if not self._series:
            return
        rect, bar_w, gap = self._bar_geometry()
        x = event.position().x()
        if x < rect.left() or x > rect.right():
            return
        idx = int((x - rect.left()) / (bar_w + gap))
        if 0 <= idx < len(self._series):
            self.bucket_clicked.emit(self._series[idx][0])
        super().mousePressEvent(event)


class CategoryBars(QWidget):
    """Horizontal category distribution bars — click to filter."""

    category_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._items: list[tuple[str, int]] = []
        self.setMinimumHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click a category to filter Events")

    def set_items(self, items: list[tuple[str, int]]) -> None:
        self._items = sorted(items, key=lambda x: -x[1])[:12]
        self.update()

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        fill_paper(painter, self.rect())
        if not self._items:
            painter.setPen(QColor(colors["muted"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No categories")
            painter.end()
            return
        max_v = max(v for _, v in self._items) or 1
        row_h = max(18, self.height() // max(1, len(self._items)))
        for i, (name, value) in enumerate(self._items):
            y = i * row_h + 4
            painter.setPen(QColor(colors["ink"]))
            painter.drawText(8, y + 14, name[:42])
            bar_x = 220
            bar_w = int((self.width() - bar_x - 60) * (value / max_v))
            painter.fillRect(bar_x, y + 2, max(2, bar_w), 14, QColor(colors["bar"]))
            painter.drawText(bar_x + bar_w + 6, y + 14, f"{value:,}")
        painter.end()

    def mousePressEvent(self, event) -> None:
        if not self._items:
            return
        row_h = max(18, self.height() // max(1, len(self._items)))
        idx = int(event.position().y() // row_h)
        if 0 <= idx < len(self._items):
            self.category_clicked.emit(self._items[idx][0])
        super().mousePressEvent(event)
