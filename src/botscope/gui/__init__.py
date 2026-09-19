"""BotScope native desktop GUI (Qt/PySide6 Observatory).

Status: IMPLEMENTED (Observatory shell) — requires optional `botscope[gui]`.

This is a local desktop application rendered with Qt widgets.
It is not a web app and does not embed a browser UI.
"""

from botscope.gui.app import launch_gui

__all__ = ["launch_gui"]
