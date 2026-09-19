"""Welcome / first-run dialog — native Qt, not a web page."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from botscope.gui.motion import fade_in
from botscope.gui.widgets import BrandMark
from botscope.ux import RecentFiles


class WelcomeAction(str, Enum):
    OPEN_LOG = "open_log"
    OPEN_SESSION = "open_session"
    OPEN_RECENT = "open_recent"
    DEMO = "demo"
    GLOBAL = "global"
    CANCEL = "cancel"


class WelcomeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to BotScope")
        self.setModal(True)
        self.resize(580, 620)
        self.action = WelcomeAction.CANCEL
        self.recent_path: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.addStretch()
        brand_row.addWidget(BrandMark(size=64))
        brand_col = QVBoxLayout()
        brand_col.setSpacing(2)
        brand = QLabel("BotScope")
        brand.setObjectName("brandTitle")
        brand_col.addWidget(brand)
        tag = QLabel("AUTOMATED TRAFFIC OBSERVATORY")
        tag.setObjectName("metricCaption")
        brand_col.addWidget(tag)
        brand_row.addLayout(brand_col)
        brand_row.addStretch()
        root.addLayout(brand_row)

        subtitle = QLabel(
            "See bot traffic on YOUR server instantly — drop a log or PCAP.\n"
            "No account. No API key. No Connect wizard."
        )
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        notice = QLabel(
            "BotScope classifies local traffic with bundled signatures + public crawler "
            "IP ranges (auto-fetched). Cloudflare Radar is an optional CDN bonus only."
        )
        notice.setWordWrap(True)
        notice.setObjectName("muted")
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(notice)

        root.addSpacing(8)
        choose = QLabel("Choose a data source")
        choose.setObjectName("sectionTitle")
        choose.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(choose)

        self._add_btn(root, "Open dataset", WelcomeAction.OPEN_LOG, primary=True)
        self._add_btn(root, "Open Analysis Session (.bscope)", WelcomeAction.OPEN_SESSION)
        self._add_btn(root, "Load sample data", WelcomeAction.DEMO)
        self._add_btn(root, "Learn how BotScope works / Global sources", WelcomeAction.GLOBAL)

        recents = RecentFiles().load().existing()[:8]
        if recents:
            root.addWidget(QLabel("Recent files:"))
            self.recent_list = QListWidget()
            for entry in recents:
                item = QListWidgetItem(f"{entry.label or Path(entry.path).name}  ·  {entry.kind}")
                item.setData(Qt.ItemDataRole.UserRole, entry.path)
                item.setToolTip(entry.path)
                self.recent_list.addItem(item)
            self.recent_list.itemDoubleClicked.connect(self._choose_recent)
            root.addWidget(self.recent_list)
            open_recent = QPushButton("Open selected recent")
            open_recent.setObjectName("ghostButton")
            open_recent.clicked.connect(self._open_selected_recent)
            root.addWidget(open_recent)

        self._add_btn(root, "Continue Empty", WelcomeAction.CANCEL)

        foot = QLabel("Network contribution defaults to OFF. No silent telemetry.")
        foot.setObjectName("muted")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(foot)
        fade_in(self, duration_ms=240)

    def _add_btn(
        self, layout: QVBoxLayout, text: str, action: WelcomeAction, *, primary: bool = False
    ) -> None:
        btn = QPushButton(text)
        if primary:
            btn.setObjectName("primaryButton")
        btn.clicked.connect(lambda: self._choose(action))
        layout.addWidget(btn)

    def _choose(self, action: WelcomeAction) -> None:
        self.action = action
        if action == WelcomeAction.CANCEL:
            self.reject()
        else:
            self.accept()

    def _choose_recent(self, item: QListWidgetItem) -> None:
        self.recent_path = item.data(Qt.ItemDataRole.UserRole)
        self.action = WelcomeAction.OPEN_RECENT
        self.accept()

    def _open_selected_recent(self) -> None:
        item = self.recent_list.currentItem() if hasattr(self, "recent_list") else None
        if item is None:
            return
        self._choose_recent(item)
