"""Session history index for recent ``.bscope`` analyses.

Status: IMPLEMENTED

Maintains a local JSON index (not network-synced) of recently opened or
saved Observatory sessions so the GUI can offer a history browser.
"""

from __future__ import annotations

from botscope.history.index import (
    HistoryEntry,
    SessionHistory,
    default_history_path,
)

__all__ = [
    "HistoryEntry",
    "SessionHistory",
    "default_history_path",
]
