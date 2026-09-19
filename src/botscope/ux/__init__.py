"""UX helpers package — recent files, settings, path classification."""

from botscope.ux.recents import (
    AppSettings,
    RecentFile,
    RecentFiles,
    classify_path,
    load_settings,
    save_settings,
    settings_path,
)

__all__ = [
    "AppSettings",
    "RecentFile",
    "RecentFiles",
    "classify_path",
    "load_settings",
    "save_settings",
    "settings_path",
]
