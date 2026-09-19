"""Source validation helpers and schema drift detection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def validate_or_schema_changed(
    data: Any,
    validator: Callable[[Any], list[str]],
    *,
    adapter: str,
) -> list[str]:
    """Run validator; prefix messages for GUI display on schema drift."""
    issues = validator(data)
    return [
        f"SOURCE SCHEMA CHANGED — Adapter: {adapter} — {msg}" if "SCHEMA" in msg.upper() or "missing" in msg.lower() else msg
        for msg in issues
    ]
