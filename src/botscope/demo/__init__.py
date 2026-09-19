"""Bundled demo corpus helpers.

Status: IMPLEMENTED — synthetic only; always label outputs as DEMO.
"""

from botscope.demo.corpus import (
    DEMO_NOTICE,
    demo_log_path,
    ensure_demo_log,
    iter_demo_events,
    write_demo_log,
)

__all__ = [
    "DEMO_NOTICE",
    "demo_log_path",
    "ensure_demo_log",
    "iter_demo_events",
    "write_demo_log",
]
