"""Highly interactive zero-config widgets — public sources, no API keys required."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from botscope.gui.theme import chart_colors
from botscope.gui.widgets import fill_paper


class ZeroConfigBanner(QFrame):
    """Always-visible clarity: what works without credentials."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("zeroConfigBanner")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        title = QLabel("ZERO-CONFIG · NO ACCOUNT · NO API KEY REQUIRED")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        body = QLabel(
            "Drop a server log or PCAP → BotScope classifies bot vs human-likely vs unknown "
            "using bundled signatures + published crawler IP ranges (fetched automatically).\n"
            "Optional only: Cloudflare Radar token unlocks CDN-wide traffic estimates — "
            "never required for YOUR server traffic."
        )
        body.setObjectName("muted")
        body.setWordWrap(True)
        layout.addWidget(body)


class SourceConstellation(QWidget):
    """Clickable orbit of public sources — interactive health map."""

    source_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._nodes: list[tuple[str, str, str]] = []  # id, label, status
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setToolTip("Click a source node to inspect it. Public sources need no API key.")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_nodes(self, nodes: list[tuple[str, str, str]]) -> None:
        self._nodes = list(nodes)
        self.update()

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill_paper(painter, self.rect())
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) * 0.36

        # Orbit guide
        painter.setPen(QPen(QColor(colors["grid"]), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # Center hub
        painter.setPen(QPen(QColor(colors["ink"]), 2))
        painter.setBrush(QColor(colors["auto"]))
        painter.drawEllipse(QPointF(cx, cy), 30, 30)
        painter.setPen(QColor(colors["paper"]))
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(
            int(cx - 40),
            int(cy - 10),
            80,
            22,
            Qt.AlignmentFlag.AlignCenter,
            "ZERO\nAUTH",
        )

        n = max(len(self._nodes), 1)
        status_color = {
            "ACTIVE": colors["auto"],
            "AVAILABLE": colors["auto"],
            "CACHED": colors["human"],
            "OFFLINE_CACHED": colors["human"],
            "DEGRADED": colors["grid"],
            "AUTH_REQUIRED": colors["muted"],
            "UNAVAILABLE": colors.get("danger", "#9b2c2c"),
            "ERROR": colors.get("danger", "#9b2c2c"),
        }
        for i, (_sid, label, status) in enumerate(self._nodes):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            painter.setPen(QPen(QColor(colors["grid"]), 1, Qt.PenStyle.DotLine))
            painter.drawLine(QPointF(cx, cy), QPointF(x, y))
            fill = QColor(status_color.get(status, colors["muted"]))
            painter.setBrush(fill)
            painter.setPen(QPen(QColor(colors["ink"]), 1.5))
            painter.drawEllipse(QPointF(x, y), 17, 17)
            painter.setPen(QColor(colors["ink"]))
            short = label if len(label) <= 14 else label[:12] + "…"
            painter.drawText(int(x - 48), int(y + 22), 96, 16, Qt.AlignmentFlag.AlignCenter, short)
        painter.end()

    def mousePressEvent(self, event) -> None:
        if not self._nodes:
            return
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) * 0.36
        n = len(self._nodes)
        px, py = event.position().x(), event.position().y()
        best = None
        best_d = 1e9
        for i, (sid, _label, _status) in enumerate(self._nodes):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best_d:
                best_d = d
                best = sid
        if best is not None and best_d < 36**2:
            self.source_clicked.emit(best)
        super().mousePressEvent(event)


class ActorOrbit(QWidget):
    """Interactive top-actors orbit — click to filter."""

    actor_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._actors: list[tuple[str, float]] = []
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click an actor to filter Events to that identity")

    def set_actors(self, actors: list[tuple[str, float]]) -> None:
        self._actors = list(actors[:10])
        self.update()

    def paintEvent(self, event) -> None:
        colors = chart_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill_paper(painter, self.rect())
        if not self._actors:
            painter.setPen(QColor(colors["muted"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No automated actors yet")
            painter.end()
            return
        cx, cy = self.width() / 2, self.height() / 2
        max_share = max(s for _, s in self._actors) or 1.0
        n = len(self._actors)
        for i, (name, share) in enumerate(self._actors):
            angle = (2 * math.pi * i / n) - math.pi / 2
            x = cx + (min(self.width(), self.height()) * 0.28) * math.cos(angle)
            y = cy + (min(self.width(), self.height()) * 0.28) * math.sin(angle)
            size = 10 + 22 * (share / max_share)
            painter.setBrush(QColor(colors["auto"]))
            painter.setPen(QPen(QColor(colors["ink"]), 1))
            painter.drawEllipse(QPointF(x, y), size, size)
            painter.setPen(QColor(colors["ink"]))
            painter.drawText(
                int(x - 50),
                int(y + size + 4),
                100,
                14,
                Qt.AlignmentFlag.AlignCenter,
                f"{name[:12]} {share * 100:.0f}%",
            )
        painter.end()

    def mousePressEvent(self, event) -> None:
        if not self._actors:
            return
        cx, cy = self.width() / 2, self.height() / 2
        dx, dy = event.position().x() - cx, event.position().y() - cy
        if dx == 0 and dy == 0:
            return
        ang = math.atan2(dy, dx)
        n = len(self._actors)
        best_i = 0
        best_diff = 1e9
        for i in range(n):
            target = (2 * math.pi * i / n) - math.pi / 2
            d = abs((ang - target + math.pi) % (2 * math.pi) - math.pi)
            if d < best_diff:
                best_diff = d
                best_i = i
        self.actor_clicked.emit(self._actors[best_i][0])
        super().mousePressEvent(event)
