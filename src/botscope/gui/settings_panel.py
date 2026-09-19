"""Settings panel — local preferences for the Observatory."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from botscope.ux import AppSettings, load_settings, save_settings


class _ThemeCard(QFrame):
    clicked = Signal(str)

    def __init__(self, theme_id: str, title: str, blurb: str, parent=None) -> None:
        super().__init__(parent)
        self.theme_id = theme_id
        self.setObjectName("themeCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        head = QLabel(title)
        head.setObjectName("sectionTitle")
        layout.addWidget(head)
        body = QLabel(blurb)
        body.setObjectName("muted")
        body.setWordWrap(True)
        layout.addWidget(body)
        preview = QLabel("Aa  ·  37.4%  ·  OBSERVED")
        preview.setObjectName("themePreview")
        if theme_id == "high_contrast":
            preview.setStyleSheet(
                "background:#000; color:#ffff00; border:2px solid #ffff00; "
                "border-radius:6px; padding:12px; font-weight:700;"
            )
        else:
            preview.setStyleSheet(
                "background:#eef3f7; color:#15202b; border:1px solid #3a8f8a; "
                "border-radius:6px; padding:12px; font-weight:600;"
            )
        layout.addWidget(preview)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit(self.theme_id)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class SettingsPanel(QWidget):
    """Edit local AppSettings (never transmitted)."""

    settings_changed = Signal(object)  # AppSettings

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings = load_settings()
        self.setObjectName("pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)
        title = QLabel("Settings")
        title.setObjectName("pageHeader")
        layout.addWidget(title)
        note = QLabel(
            "Preferences stay on this machine. Network contribution remains OFF "
            "unless you enable it elsewhere."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addWidget(QLabel("Appearance"))
        cards = QHBoxLayout()
        self.card_instrument = _ThemeCard(
            "instrument",
            "Instrument",
            "Slate + teal measurement console — default observatory look.",
        )
        self.card_contrast = _ThemeCard(
            "high_contrast",
            "High contrast",
            "Yellow on black — stronger focus rings and larger type.",
        )
        self.card_instrument.clicked.connect(self._pick_theme)
        self.card_contrast.clicked.connect(self._pick_theme)
        cards.addWidget(self.card_instrument)
        cards.addWidget(self.card_contrast)
        layout.addLayout(cards)

        form = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItems(["instrument", "high_contrast"])
        self.theme.setCurrentText(self._settings.theme)
        self.theme.currentTextChanged.connect(self._on_theme_combo)
        form.addRow("Theme:", self.theme)
        self._sync_theme_cards()

        self.denominator = QComboBox()
        self.denominator.addItems(["requests", "bytes"])
        self.denominator.setCurrentText(self._settings.default_denominator)
        form.addRow("Default denominator:", self.denominator)

        self.reduce_motion = QCheckBox("Reduce motion (disable fades & pulses)")
        self.reduce_motion.setChecked(getattr(self._settings, "reduce_motion", False))
        self.chart_animation = QCheckBox("Chart animation")
        self.chart_animation.setChecked(getattr(self._settings, "chart_animation", True))
        self.auto_refresh_sources = QCheckBox("Automatic source refresh while running")
        self.auto_refresh_sources.setChecked(
            getattr(self._settings, "auto_refresh_sources", True)
        )
        self.density = QComboBox()
        self.density.addItems(["comfortable", "compact"])
        self.density.setCurrentText(getattr(self._settings, "interface_density", "comfortable"))
        form.addRow("Interface density:", self.density)
        self.hash_ips = QCheckBox("Hash IP addresses on ingest")
        self.hash_ips.setChecked(self._settings.hash_ips)
        self.truncate_ips = QCheckBox("Truncate IP addresses on ingest")
        self.truncate_ips.setChecked(self._settings.truncate_ips)
        self.redact_query = QCheckBox("Redact sensitive query parameters")
        self.redact_query.setChecked(self._settings.redact_query)
        self.show_welcome = QCheckBox("Show welcome dialog on launch")
        self.show_welcome.setChecked(self._settings.show_welcome)
        self.open_last = QCheckBox("Re-open last session on launch (when available)")
        self.open_last.setChecked(self._settings.open_last_session_on_start)
        for w in (
            self.reduce_motion,
            self.chart_animation,
            self.auto_refresh_sources,
            self.hash_ips,
            self.truncate_ips,
            self.redact_query,
            self.show_welcome,
            self.open_last,
        ):
            form.addRow(w)

        self.cf_token = QLineEdit()
        self.cf_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.cf_token.setPlaceholderText("OPTIONAL — leave blank; not needed for your server logs")
        if self._settings.cloudflare_radar_token:
            self.cf_token.setText(self._settings.cloudflare_radar_token)
        form.addRow("Cloudflare Radar (optional bonus):", self.cf_token)
        layout.addLayout(form)

        privacy = QLabel(
            "Privacy & credentials\n"
            "• Account required: No\n"
            "• Cloud profile: No\n"
            "• API keys required for YOUR server traffic: None\n"
            "• Public crawler IP / identity feeds: automatic (zero-auth)\n"
            "• Optional only: Cloudflare Radar token (CDN estimates — not your logs)\n"
            "• Preferences: stored locally"
        )
        privacy.setObjectName("muted")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)

        keys = QLabel(
            "API KEY CHEAT SHEET\n"
            "Required: (none)\n"
            "Optional: Cloudflare Radar Read token — Settings field above. "
            "Unlocks Global Observatory CDN bot/human estimates only."
        )
        keys.setWordWrap(True)
        layout.addWidget(keys)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        preview_btn = QPushButton("Apply theme now")
        preview_btn.setObjectName("ghostButton")
        preview_btn.setToolTip("Apply the selected theme without leaving Settings")
        preview_btn.clicked.connect(self._apply_preview)
        reset_btn = QPushButton("Reset BotScope settings")
        reset_btn.setObjectName("ghostButton")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(preview_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()

    def _sync_theme_cards(self) -> None:
        current = self.theme.currentText()
        self.card_instrument.set_selected(current == "instrument")
        self.card_contrast.set_selected(current == "high_contrast")

    def _pick_theme(self, theme_id: str) -> None:
        self.theme.setCurrentText(theme_id)
        self._sync_theme_cards()

    def _on_theme_combo(self, _text: str) -> None:
        self._sync_theme_cards()

    def _build_settings(self) -> AppSettings:
        token = self.cf_token.text().strip() or None
        return AppSettings(
            theme=self.theme.currentText(),
            hash_ips=self.hash_ips.isChecked(),
            truncate_ips=self.truncate_ips.isChecked(),
            redact_query=self.redact_query.isChecked(),
            open_last_session_on_start=self.open_last.isChecked(),
            show_welcome=self.show_welcome.isChecked(),
            default_denominator=self.denominator.currentText(),
            cloudflare_radar_token=token,
            reduce_motion=self.reduce_motion.isChecked(),
            chart_animation=self.chart_animation.isChecked(),
            auto_refresh_sources=self.auto_refresh_sources.isChecked(),
            interface_density=self.density.currentText(),
            last_page_id=getattr(self._settings, "last_page_id", "observatory"),
            sidebar_collapsed=getattr(self._settings, "sidebar_collapsed", False),
            sidebar_width=getattr(self._settings, "sidebar_width", 220),
        )

    def _apply_preview(self) -> None:
        self.settings_changed.emit(self._build_settings())

    def _reset(self) -> None:
        self._settings = AppSettings()
        save_settings(self._settings)
        self.theme.setCurrentText(self._settings.theme)
        self.denominator.setCurrentText(self._settings.default_denominator)
        self.density.setCurrentText(self._settings.interface_density)
        self.reduce_motion.setChecked(False)
        self.chart_animation.setChecked(True)
        self.auto_refresh_sources.setChecked(True)
        self.hash_ips.setChecked(False)
        self.truncate_ips.setChecked(False)
        self.redact_query.setChecked(True)
        self.show_welcome.setChecked(True)
        self.open_last.setChecked(False)
        self.cf_token.clear()
        self.settings_changed.emit(self._settings)

    def _save(self) -> None:
        self._settings = self._build_settings()
        save_settings(self._settings)
        self.settings_changed.emit(self._settings)
