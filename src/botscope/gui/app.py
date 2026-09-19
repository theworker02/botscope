"""Launch the native BotScope Observatory (Qt desktop — not a website)."""

from __future__ import annotations

import sys


def launch_gui(*, show_welcome: bool | None = None) -> None:
    """Start the Observatory as a local desktop application."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise SystemExit(
            "GUI requires PySide6. Install with:\n"
            "  pip install 'botscope[gui]'\n"
            "Then run: botscope   or   botscope gui"
        ) from exc

    # Security gate (lockout + vault tamper) before loading settings / window.
    from botscope.ux.tamper import enforce_gui_security_gate

    enforce_gui_security_gate()

    from botscope.gui.main_window import ObservatoryWindow
    from botscope.gui.motion import set_reduce_motion
    from botscope.gui.theme import apply_application_font, set_chart_theme, stylesheet_for
    from botscope.ux import load_settings

    settings = load_settings()
    app = QApplication(sys.argv)
    app.setApplicationName("BotScope")
    app.setOrganizationName("BotScope")
    app.setStyle("Fusion")
    apply_application_font(app)
    set_chart_theme(settings.theme)
    set_reduce_motion(settings.reduce_motion)
    app.setStyleSheet(stylesheet_for(settings.theme))

    win = ObservatoryWindow(settings=settings)
    win.show()
    do_welcome = settings.show_welcome if show_welcome is None else show_welcome
    if do_welcome:
        win.show_welcome()
    elif settings.open_last_session_on_start:
        win.maybe_open_last_session()
    raise SystemExit(app.exec())
