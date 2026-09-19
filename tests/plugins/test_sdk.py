"""Plugin SDK tests."""

from __future__ import annotations

from pathlib import Path

from botscope.plugins.sdk import create_plugin_scaffold, validate_plugin_dir


def test_scaffold_and_validate(tmp_path: Path):
    root = create_plugin_scaffold(tmp_path, name="unit")
    issues = validate_plugin_dir(root)
    assert not any(i.severity == "error" for i in issues)
