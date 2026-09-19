"""High-contrast Observatory theme — accessibility-first, full coverage."""

from __future__ import annotations

HIGH_CONTRAST = """
QWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: "Bahnschrift", "Segoe UI Semibold", "Segoe UI", "IBM Plex Sans", sans-serif;
    font-size: 14px;
}
QMainWindow, QDialog {
    background-color: #000000;
}
QWidget#pageRoot {
    background-color: #000000;
}
QWidget#pageRoot QLabel#pageHeader {
    font-size: 20px;
    font-weight: 800;
    color: #ffff00;
    padding: 2px 0 6px 0;
}
QMenuBar, QToolBar, QStatusBar {
    background-color: #0a0a0a;
    color: #ffffff;
    border-bottom: 2px solid #ffff00;
    padding: 6px;
}
QMenuBar::item:selected, QMenu::item:selected {
    background-color: #ffff00;
    color: #000000;
}
QMenu {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffff00;
}
QToolBar QToolButton, QToolBar QPushButton {
    background-color: #111111;
    color: #ffffff;
    border: 2px solid #ffff00;
    border-radius: 4px;
    padding: 8px 14px;
    font-weight: 700;
}
QToolBar QToolButton:hover, QToolBar QPushButton:hover,
QToolBar QToolButton:pressed, QToolBar QPushButton:pressed {
    background-color: #ffff00;
    color: #000000;
}
QToolBar QLabel {
    color: #ffff66;
    font-weight: 700;
}
QToolBar QComboBox {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffff00;
    padding: 5px 10px;
}
QPushButton {
    background-color: #111111;
    color: #ffffff;
    border: 2px solid #ffff00;
    border-radius: 4px;
    padding: 10px 16px;
    font-weight: 700;
    min-height: 22px;
}
QPushButton:hover, QPushButton:pressed {
    background-color: #ffff00;
    color: #000000;
}
QPushButton:disabled {
    background-color: #333333;
    color: #888888;
    border-color: #666666;
}
QPushButton:focus {
    border: 3px solid #ffffff;
}
QPushButton#primaryButton {
    background-color: #ffff00;
    color: #000000;
    border: 2px solid #ffffff;
    font-weight: 800;
}
QPushButton#primaryButton:hover {
    background-color: #ffffff;
    color: #000000;
    border-color: #ffff00;
}
QPushButton#ghostButton {
    background-color: #000000;
    color: #ffff00;
    border: 2px solid #ffff00;
}
QPushButton#ghostButton:hover {
    background-color: #ffff00;
    color: #000000;
}
QPushButton#dangerButton {
    background-color: #000000;
    color: #ff4444;
    border: 2px solid #ff4444;
}
QPushButton#dangerButton:hover {
    background-color: #ff4444;
    color: #000000;
}
QToolButton#ghostButton {
    background-color: #000000;
    color: #ffff00;
    border: 2px solid #ffff00;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: 800;
}
QListWidget, QTreeWidget, QTableWidget, QTableView, QTextEdit, QPlainTextEdit {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    selection-background-color: #ffff00;
    selection-color: #000000;
}
QHeaderView::section {
    background-color: #111111;
    color: #ffff00;
    border: 1px solid #ffffff;
    padding: 8px;
    font-weight: 700;
}
QComboBox, QLineEdit, QSpinBox {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ffffff;
    border-radius: 2px;
    padding: 6px 10px;
}
QComboBox:focus, QLineEdit:focus {
    border: 2px solid #ffff00;
}
QCheckBox {
    color: #ffffff;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #ffff00;
    background: #000000;
}
QCheckBox::indicator:checked {
    background-color: #ffff00;
}
QGroupBox {
    border: 2px solid #ffffff;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 700;
    color: #ffff00;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px;
    color: #ffff00;
}
QFrame#sectionPanel, QWidget#sectionPanel {
    background-color: #0a0a0a;
    border: 2px solid #ffffff;
}
QFrame#zeroConfigBanner {
    background-color: #0a0a0a;
    border: 2px solid #ffff00;
    border-left: 6px solid #ffff00;
}
QWidget#emptyState {
    background-color: #0a0a0a;
    border: 2px dashed #ffff00;
}
QLabel#brandTitle {
    font-size: 28px;
    font-weight: 800;
    color: #ffff00;
}
QLabel#brandWordmark {
    font-size: 22px;
    font-weight: 800;
    color: #ffff00;
    padding: 14px 8px 4px 14px;
}
QLabel#brandTagline {
    font-size: 11px;
    font-weight: 800;
    color: #ffff66;
    letter-spacing: 1.2px;
    padding: 0 8px 10px 14px;
}
QLabel#navSourceInfo {
    color: #cccccc;
    padding: 10px 14px;
}
QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 800;
    color: #ffff00;
}
QLabel#metricValue {
    font-size: 30px;
    font-weight: 800;
    color: #ffffff;
    font-family: "Cascadia Mono", "Consolas", monospace;
}
QLabel#metricCaption {
    font-size: 12px;
    color: #ffff66;
    letter-spacing: 1px;
    font-weight: 700;
}
QLabel#provenanceBadge {
    background-color: #000000;
    color: #00ff66;
    border: 2px solid #00ff66;
    border-radius: 2px;
    padding: 4px 10px;
    font-weight: 800;
}
QLabel#demoBanner {
    background-color: #ffff00;
    color: #000000;
    border: 2px solid #ffffff;
    font-weight: 800;
    padding: 10px;
}
QLabel#muted { color: #cccccc; }
QLabel#statusChip {
    color: #ffff00;
    font-weight: 800;
    border: 1px solid #ffff00;
    padding: 3px 10px;
}
QFrame#metricTile {
    background-color: #0a0a0a;
    border: 2px solid #ffffff;
    border-radius: 4px;
}
QFrame#metricTile:hover {
    border-color: #ffff00;
}
QFrame#themeCard {
    background-color: #0a0a0a;
    border: 2px solid #ffffff;
}
QFrame#themeCard[selected="true"] {
    border-color: #ffff00;
    background-color: #1a1a00;
}
QWidget#navChrome {
    background-color: #0a0a0a;
    border-right: 2px solid #ffff00;
}
QListWidget#navList {
    background-color: #0a0a0a;
    color: #ffffff;
    border: none;
}
QListWidget#navList::item {
    padding: 12px 16px;
    margin: 2px 4px;
}
QListWidget#navList::item:selected {
    background-color: #ffff00;
    color: #000000;
    font-weight: 800;
}
QListWidget#navList::item:hover:!selected {
    background-color: #222200;
    color: #ffff00;
}
QListWidget#navList::item:!enabled {
    color: #ffff66;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 1px;
    background: transparent;
}
QTabWidget::pane {
    border: 2px solid #ffffff;
    background-color: #000000;
}
QTabBar::tab {
    background-color: #111111;
    color: #ffffff;
    border: 2px solid #ffffff;
    padding: 10px 16px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffff00;
    color: #000000;
    font-weight: 800;
}
QProgressBar {
    border: 2px solid #ffffff;
    background: #000000;
    text-align: center;
    color: #ffffff;
}
QProgressBar::chunk {
    background-color: #ffff00;
}
QScrollBar:vertical {
    background: #000000;
    width: 12px;
    border: 1px solid #ffffff;
}
QScrollBar::handle:vertical {
    background: #ffff00;
    min-height: 28px;
}
QStatusBar {
    color: #ffff66;
}
"""
