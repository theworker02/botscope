"""BotScope GUI visual identity — scientific observatory instrument look."""

from __future__ import annotations

# Chart / painter colors keyed by theme id (stylesheets cannot style QPainter).
CHART_PALETTE = {
    "instrument": {
        "paper": "#eef3f7",
        "paper_deep": "#dfe8ef",
        "ink": "#15202b",
        "muted": "#5a6d7e",
        "grid": "#a8b8c6",
        "auto": "#2f6f6b",
        "human": "#3d6a8c",
        "total": "#c2ced9",
        "bar": "#2f6f6b",
        "accent": "#3a8f8a",
        "accent_bright": "#5ec4bd",
        "warn": "#c9a227",
        "danger": "#9b2c2c",
    },
    "high_contrast": {
        "paper": "#000000",
        "paper_deep": "#0a0a0a",
        "ink": "#ffffff",
        "muted": "#ffff66",
        "grid": "#ffffff",
        "auto": "#ffff00",
        "human": "#00ffff",
        "total": "#666666",
        "bar": "#ffff00",
        "accent": "#ffff00",
        "accent_bright": "#ffffff",
        "warn": "#ffff00",
        "danger": "#ff4444",
    },
}

_ACTIVE_CHART_THEME = "instrument"

# Named palette constants for Python-side chrome (keep in sync with STYLESHEET).
ACCENT = "#3a8f8a"
ACCENT_BRIGHT = "#5ec4bd"
INK = "#15202b"
INK_SOFT = "#1e2d3d"
PAPER = "#eef3f7"
PAPER_DEEP = "#dfe8ef"
CHROME = "#1a2836"
CHROME_MID = "#243447"
NAV_FG = "#d8e2eb"
MUTED = "#5a6d7e"


def set_chart_theme(theme: str) -> None:
    global _ACTIVE_CHART_THEME
    _ACTIVE_CHART_THEME = theme if theme in CHART_PALETTE else "instrument"


def chart_colors() -> dict[str, str]:
    return CHART_PALETTE.get(_ACTIVE_CHART_THEME, CHART_PALETTE["instrument"])


def stylesheet_for(theme: str) -> str:
    from botscope.gui.theme_contrast import HIGH_CONTRAST

    if theme == "high_contrast":
        return HIGH_CONTRAST
    return STYLESHEET


STYLESHEET = """
/* ── Base ─────────────────────────────────────────────────────────── */
QWidget {
    background-color: #e4ebf1;
    color: #15202b;
    font-family: "Bahnschrift", "Segoe UI Semibold", "Segoe UI", "IBM Plex Sans", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #d5dee7;
}
QWidget#pageRoot {
    background-color: #e4ebf1;
}
QWidget#pageRoot QLabel#pageHeader {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.4px;
    color: #15202b;
    padding: 2px 0 6px 0;
}

/* ── Menus / chrome ───────────────────────────────────────────────── */
QMenuBar {
    background-color: #15202b;
    color: #d8e2eb;
    padding: 5px 6px;
    border-bottom: 1px solid #2a3d52;
}
QMenuBar::item {
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected { background-color: #2c3b4f; }
QMenu {
    background-color: #1e2d3d;
    color: #d8e2eb;
    border: 1px solid #3d5168;
    padding: 4px;
}
QMenu::item {
    padding: 7px 28px 7px 16px;
    border-radius: 4px;
}
QMenu::item:selected { background-color: #3a8f8a; }
QMenu::separator {
    height: 1px;
    background: #3d5168;
    margin: 4px 8px;
}

QToolBar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e2d3d, stop:1 #15202b);
    spacing: 8px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #2a3d52;
}
QToolBar QToolButton, QToolBar QPushButton {
    background-color: #2c3b4f;
    color: #e8eef2;
    border: 1px solid #4a6078;
    border-radius: 5px;
    padding: 7px 14px;
    font-weight: 600;
    min-height: 18px;
}
QToolBar QToolButton:hover, QToolBar QPushButton:hover {
    background-color: #3a8f8a;
    border-color: #5ec4bd;
}
QToolBar QToolButton:pressed, QToolBar QPushButton:pressed {
    background-color: #245e5a;
}
QToolBar QLabel {
    color: #9aabba;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    padding-left: 6px;
}
QToolBar QComboBox {
    background-color: #243447;
    color: #e8eef2;
    border: 1px solid #4a6078;
    border-radius: 4px;
    padding: 5px 10px;
    min-width: 140px;
}
QToolBar QComboBox:hover { border-color: #5ec4bd; }
QToolBar QComboBox::drop-down { border: none; width: 20px; }

QStatusBar {
    background-color: #15202b;
    color: #9aabba;
    border-top: 1px solid #2a3d52;
    padding: 2px 6px;
}
QStatusBar QLabel {
    color: #b8c5d4;
    font-size: 12px;
}

QSplitter::handle {
    background-color: #9aabba;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover { background-color: #3a8f8a; }

/* ── Sidebar / nav ────────────────────────────────────────────────── */
QWidget#navChrome {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e2d3d, stop:1 #15202b);
}
QLabel#brandWordmark {
    font-size: 20px;
    font-weight: 700;
    color: #e8eef2;
    letter-spacing: 0.8px;
    padding: 14px 8px 4px 14px;
}
QLabel#brandTagline {
    font-size: 10px;
    font-weight: 600;
    color: #5ec4bd;
    letter-spacing: 1.2px;
    padding: 0 8px 10px 14px;
}
QLabel#navSourceInfo {
    color: #9aabba;
    font-size: 11px;
    padding: 10px 14px 14px 14px;
}
QListWidget#navList {
    background-color: transparent;
    color: #d8e2eb;
    border: none;
    outline: none;
    border-radius: 0;
    padding: 4px 0;
}
QListWidget#navList::item {
    padding: 10px 14px;
    border-radius: 5px;
    margin: 1px 8px;
}
QListWidget#navList::item:selected {
    background-color: #3a8f8a;
    color: #ffffff;
    font-weight: 700;
}
QListWidget#navList::item:hover:!selected {
    background-color: #2c3b4f;
}
QListWidget#navList::item:!enabled {
    color: #6a7d90;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.1px;
    padding: 12px 14px 4px 14px;
    margin: 6px 8px 0 8px;
    background: transparent;
}

/* ── Surfaces / tables ────────────────────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget, QTableView, QTextEdit, QPlainTextEdit {
    background-color: #eef3f7;
    border: 1px solid #b0bec9;
    border-radius: 6px;
    selection-background-color: #3a8f8a;
    selection-color: #ffffff;
    padding: 2px;
}
QHeaderView::section {
    background-color: #1e2d3d;
    color: #d8e2eb;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #2a3d52;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.3px;
}

/* ── Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1e2d3d;
    color: #e8eef2;
    border: 1px solid #3d5168;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 600;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #2c3b4f;
    border-color: #5a7a96;
}
QPushButton:pressed {
    background-color: #15202b;
}
QPushButton:disabled {
    background-color: #9aa8b5;
    color: #e8eef2;
    border-color: #9aa8b5;
}
QPushButton:focus {
    border: 2px solid #5ec4bd;
}
QPushButton#primaryButton {
    background-color: #2f6f6b;
    border: 1px solid #3a8f8a;
    color: #ffffff;
    font-weight: 700;
    letter-spacing: 0.3px;
}
QPushButton#primaryButton:hover {
    background-color: #3a8f8a;
    border-color: #5ec4bd;
}
QPushButton#primaryButton:pressed {
    background-color: #245e5a;
}
QPushButton#ghostButton {
    background-color: transparent;
    color: #15202b;
    border: 1.5px solid #3a8f8a;
}
QPushButton#ghostButton:hover {
    background-color: #d5e8e6;
    color: #1f4f4c;
}
QPushButton#dangerButton {
    background-color: #8b3a3a;
    border: 1px solid #a84848;
    color: #ffffff;
}
QPushButton#dangerButton:hover { background-color: #a84848; }
QToolButton#ghostButton {
    background-color: #d5e8e6;
    color: #1f4f4c;
    border: 1px solid #3a8f8a;
    border-radius: 12px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: 12px;
}
QToolButton#ghostButton:hover {
    background-color: #3a8f8a;
    color: #ffffff;
}

/* ── Inputs ───────────────────────────────────────────────────────── */
QComboBox, QLineEdit, QSpinBox {
    background-color: #eef3f7;
    border: 1px solid #b0bec9;
    border-radius: 5px;
    padding: 7px 10px;
    min-height: 18px;
    selection-background-color: #3a8f8a;
}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover {
    border-color: #3a8f8a;
}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #3a8f8a;
    padding: 6px 9px;
}
QCheckBox {
    spacing: 8px;
    padding: 4px 0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #3d5168;
    border-radius: 3px;
    background: #eef3f7;
}
QCheckBox::indicator:checked {
    background-color: #2f6f6b;
    border-color: #2f6f6b;
}
QCheckBox::indicator:hover {
    border-color: #3a8f8a;
}

/* ── Group / section panels ───────────────────────────────────────── */
QGroupBox {
    font-weight: 700;
    border: 1px solid #b0bec9;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #eaf0f5;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #15202b;
}
QFrame#sectionPanel, QWidget#sectionPanel {
    background-color: #eaf0f5;
    border: 1px solid #b8c5d0;
    border-radius: 8px;
}
QFrame#sectionPanel:hover, QWidget#sectionPanel:hover {
    border-color: #9aabba;
}

/* ── Typography / badges ──────────────────────────────────────────── */
QLabel#statusChip {
    font-size: 12px;
    font-weight: 600;
    color: #5a6d7e;
    padding: 3px 10px;
    border-radius: 10px;
    background-color: #d8e2eb;
}
QLabel#brandTitle {
    font-size: 28px;
    font-weight: 700;
    color: #15202b;
    letter-spacing: 0.8px;
}
QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #15202b;
    letter-spacing: 0.2px;
}
QLabel#metricValue {
    font-size: 28px;
    font-weight: 700;
    color: #15202b;
    font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
}
QLabel#metricCaption {
    font-size: 11px;
    color: #5a6d7e;
    letter-spacing: 1.0px;
    font-weight: 700;
}
QLabel#provenanceBadge {
    background-color: #d5e8e6;
    color: #1f4f4c;
    border: 1px solid #3a8f8a;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}
QLabel#demoBanner {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f7e6b8, stop:1 #f0d98a);
    color: #5c4206;
    border: 1px solid #c9a227;
    border-radius: 6px;
    padding: 10px 14px;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.3px;
}
QLabel#muted { color: #5a6d7e; }
QLabel#themePreview {
    border-radius: 8px;
    padding: 16px;
    font-weight: 600;
}
QFrame#zeroConfigBanner {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e2efed, stop:1 #eaf0f5);
    border: 1px solid #3a8f8a;
    border-left: 4px solid #2f6f6b;
    border-radius: 6px;
}
QWidget#emptyState {
    background-color: #eaf0f5;
    border: 1px dashed #9aabba;
    border-radius: 10px;
}

/* ── Metric tiles / theme cards ───────────────────────────────────── */
QFrame#metricTile {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f5f8fb, stop:1 #e8eef3);
    border: 1px solid #b0bec9;
    border-radius: 8px;
}
QFrame#metricTile:hover {
    border-color: #3a8f8a;
    background-color: #f0f7f6;
}
QFrame#themeCard {
    background-color: #eef3f7;
    border: 2px solid #b0bec9;
    border-radius: 8px;
}
QFrame#themeCard[selected="true"] {
    border-color: #2f6f6b;
    background-color: #d5e8e6;
}

/* ── Tabs (hidden bar still styled if shown) ──────────────────────── */
QTabWidget::pane {
    border: 1px solid #b0bec9;
    border-radius: 6px;
    background-color: #e4ebf1;
}
QTabBar::tab {
    background-color: #c9d5e0;
    color: #15202b;
    padding: 9px 16px;
    border: 1px solid #b0bec9;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background-color: #eef3f7;
    font-weight: 700;
}
QTabBar::tab:hover:!selected {
    background-color: #d5dde6;
}

/* ── Progress / scroll ────────────────────────────────────────────── */
QProgressBar {
    border: 1px solid #b0bec9;
    border-radius: 4px;
    text-align: center;
    background: #eef3f7;
    min-height: 12px;
    color: #15202b;
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2f6f6b, stop:1 #5ec4bd);
    border-radius: 3px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    background: #e4ebf1;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #9aabba;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #3a8f8a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
