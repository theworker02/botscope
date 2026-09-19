"""Validate a plugin directory layout.

Status: IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationIssue:
    severity: str  # error | warning | info
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "message": self.message}


def validate_plugin_dir(path: str | Path) -> list[ValidationIssue]:
    root = Path(path)
    issues: list[ValidationIssue] = []
    if not root.exists():
        return [ValidationIssue("error", f"Path does not exist: {root}")]
    if not (root / "pyproject.toml").exists():
        issues.append(ValidationIssue("warning", "Missing pyproject.toml"))
    py_files = list(root.rglob("plugin.py")) + list(root.rglob("*plugin*.py"))
    # de-dup
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in py_files:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    if not unique:
        issues.append(ValidationIssue("error", "No plugin.py (or *plugin*.py) found"))
    else:
        issues.append(
            ValidationIssue("info", f"Found plugin module(s): {[str(p) for p in unique]}")
        )
    if not (root / "README.md").exists():
        issues.append(ValidationIssue("warning", "Missing README.md"))
    if not any(i.severity == "error" for i in issues):
        issues.append(ValidationIssue("info", "Basic layout looks OK"))
    return issues
