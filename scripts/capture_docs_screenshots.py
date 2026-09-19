#!/usr/bin/env python3
"""Capture Observatory GUI screenshots for public documentation.

Usage (from repo root, with GUI extras installed):

    python scripts/capture_docs_screenshots.py

Writes PNGs under docs/assets/screenshots/. Clears any Cloudflare token
field before capturing Settings so no secrets appear in docs assets.

Forces Segoe UI so labels never render as empty tofu boxes.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "screenshots"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _assert_text_readable(path: Path) -> None:
    """Fail fast if the grab looks like tofu-box font failure."""
    from PIL import Image, ImageStat

    im = Image.open(path).convert("RGB")
    w, h = im.size
    # Probe several content bands — pages differ in where labels sit.
    bands = [
        (0.28, 0.10, 0.75, 0.22),
        (0.28, 0.22, 0.75, 0.40),
        (0.28, 0.40, 0.70, 0.58),
    ]
    best_spread = 0
    best_ink = 0
    for left, top, right, bottom in bands:
        band = im.crop((int(w * left), int(h * top), int(w * right), int(h * bottom)))
        gray = band.convert("L")
        extrema = gray.getextrema()
        spread = (extrema[1] - extrema[0]) if extrema else 0
        pixels = list(gray.getdata())
        ink = sum(1 for v in pixels if v < 90)
        best_spread = max(best_spread, spread)
        best_ink = max(best_ink, ink)
    # Tofu-box failures are nearly flat (spread ~0). Real UI has strong contrast.
    if best_spread < 40:
        raise SystemExit(
            f"ERROR: {path.name} looks unreadable "
            f"(spread={best_spread}, ink={best_ink}). Refusing overwrite."
        )


def main() -> int:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QApplication, QLineEdit

    from botscope.gui.main_window import ObservatoryWindow
    from botscope.gui.motion import set_reduce_motion
    from botscope.gui.navigation import page_index
    from botscope.gui.theme import apply_application_font, set_chart_theme, stylesheet_for
    from botscope.ux import load_settings

    OUT.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    capture_settings = replace(
        settings,
        show_welcome=False,
        open_last_session_on_start=False,
        reduce_motion=True,
        chart_animation=False,
        sidebar_collapsed=False,
        sidebar_width=220,
        theme="instrument",
        cloudflare_radar_token=None,
    )

    # Prefer crisp integer DPI for documentation grabs.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("BotScope")
    app.setOrganizationName("BotScope")
    app.setStyle("Fusion")
    apply_application_font(app)
    set_chart_theme(capture_settings.theme)
    set_reduce_motion(True)
    app.setStyleSheet(stylesheet_for(capture_settings.theme))

    win = ObservatoryWindow(settings=capture_settings)
    win.resize(1440, 900)
    win._sidebar_collapsed = False
    win.nav_collapse_btn.setText("«")
    if hasattr(win, "_set_nav_collapsed_labels"):
        win._set_nav_collapsed_labels(False)
    win._nav_wrap.setMinimumWidth(200)
    win._nav_wrap.setMaximumWidth(280)
    win._nav_splitter.setSizes([220, 1220])
    win.show()
    win.raise_()
    win.activateWindow()
    win._nav_splitter.setSizes([220, 1220])
    app.processEvents()

    shots: list[tuple[str, str]] = [
        ("observatory", "observatory-dashboard.png"),
        ("global", "global-observatory.png"),
        ("events", "events.png"),
        ("bot_library", "bot-library.png"),
        ("sources", "sources.png"),
        ("settings", "settings.png"),
    ]

    state = {"phase": "load_demo", "attempts": 0}

    def grab(name: str) -> None:
        app.processEvents()
        path = OUT / name
        # QWidget.grab() is reliable once fonts are registered into QFontDatabase.
        pix = win.grab()
        if pix.isNull() or pix.width() < 400:
            raise SystemExit(f"ERROR: null/empty grab for {name}")
        pix.save(str(path), "PNG")
        _assert_text_readable(path)
        print(f"wrote {path} ({pix.width()}x{pix.height()})")

    def tick() -> None:
        phase = state["phase"]
        if phase == "load_demo":
            win.load_demo()
            state["phase"] = "wait_demo"
            return

        if phase == "wait_demo":
            state["attempts"] += 1
            ready = (
                win.session.result is not None
                and win.session.is_demo
                and not (win._worker and win._worker.isRunning())
            )
            if not ready:
                if state["attempts"] > 200:
                    print("ERROR: demo load timed out", file=sys.stderr)
                    app.quit()
                    return
                return
            state["phase"] = "shots"
            state["shot_i"] = 0
            state["settle"] = 0
            return

        if phase == "shots":
            i = state["shot_i"]
            if i >= len(shots):
                app.quit()
                return
            page_id, filename = shots[i]
            settle = state["settle"]
            if settle == 0:
                win.tabs.setCurrentIndex(page_index(page_id))
                if page_id == "settings":
                    token = win.settings_panel.cf_token
                    token.clear()
                    token.setEchoMode(QLineEdit.EchoMode.Password)
                    token.setPlaceholderText(
                        "OPTIONAL — leave blank; not needed for your server logs"
                    )
                state["settle"] = 1
                return
            # Longer settle so layout + fonts fully paint before grab.
            if settle < 8:
                state["settle"] = settle + 1
                return
            grab(filename)
            state["shot_i"] = i + 1
            state["settle"] = 0
            return

    timer = QTimer()
    timer.setInterval(200)
    timer.timeout.connect(tick)
    timer.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
