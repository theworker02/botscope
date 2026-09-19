"""Analysis Workspace persistence.

Status: IMPLEMENTED

Serializes Observatory view state (filters, denominator, chart overlays,
column prefs, annotations refs, time range) into JSON suitable for
embedding in ``.bscope`` session config or a ``workspace.json`` sidecar.
"""

from __future__ import annotations

from botscope.workspace.state import (
    AnalysisWorkspace,
    ChartOverlay,
    ColumnPref,
    TimeRange,
    WorkspaceError,
    load_workspace,
    save_workspace,
)

__all__ = [
    "AnalysisWorkspace",
    "ChartOverlay",
    "ColumnPref",
    "TimeRange",
    "WorkspaceError",
    "load_workspace",
    "save_workspace",
]
