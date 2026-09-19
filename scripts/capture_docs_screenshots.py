#!/usr/bin/env python3
"""Capture Observatory GUI screenshots for public documentation.

Usage (from repo root, with GUI extras installed):

    python scripts/capture_docs_screenshots.py

Writes PNGs under docs/assets/screenshots/. Clears any Cloudflare token
field before capturing Settings so no secrets appear in docs assets.
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


def main() -> int:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QLineEdit

    # Avoid welcome dialog / last-session reopen during capture.
    from botscope.gui.main_window import ObservatoryWindow
    from botscope.gui.motion import set_reduce_motion
    from botscope.gui.navigation import page_index
    from botscope.gui.theme import set_chart_theme, stylesheet_for
    from botscope.ux import load_settings

    OUT.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    capture_settings = replace(
        settings,
        show_welcome=False,
        open_last_session_on_start=False,
        reduce_motion=True,
        chart_animation=False,
        # Docs shots should show full branded sidebar, not a collapsed strip.
        sidebar_collapsed=False,
        sidebar_width=220,
        theme="instrument",
        # Never render a real token into docs screenshots.
        cloudflare_radar_token=None,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BotScope")
    app.setOrganizationName("BotScope")
    app.setStyle("Fusion")
    set_chart_theme(capture_settings.theme)
    set_reduce_motion(True)
    app.setStyleSheet(stylesheet_for(capture_settings.theme))

    win = ObservatoryWindow(settings=capture_settings)
    win.resize(1440, 900)
    # Force expanded branded sidebar for documentation shots.
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
    # Re-assert sizes after show (layout may clamp before first paint).
    win._nav_splitter.setSizes([220, 1220])

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
        path = OUT / name
        pix = win.grab()
        pix.save(str(path), "PNG")
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
                    # Ensure token field is empty/masked placeholder only.
                    token = win.settings_panel.cf_token
                    token.clear()
                    token.setEchoMode(QLineEdit.EchoMode.Password)
                    token.setPlaceholderText(
                        "OPTIONAL — leave blank; not needed for your server logs"
                    )
                elif page_id == "global":
                    # Give Global panel a moment to paint status chips.
                    pass
                state["settle"] = 1
                return
            if settle < 3:
                state["settle"] = settle + 1
                return
            grab(filename)
            state["shot_i"] = i + 1
            state["settle"] = 0
            return

    timer = QTimer()
    timer.setInterval(150)
    timer.timeout.connect(tick)
    timer.start()
    # Kick off after the event loop starts.
    QTimer.singleShot(400, lambda: None)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
