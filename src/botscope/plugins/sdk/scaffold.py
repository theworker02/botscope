"""Create a local plugin scaffold.

Status: IMPLEMENTED
"""

from __future__ import annotations

from pathlib import Path

_PLUGIN_TEMPLATE = '''from __future__ import annotations

from botscope.normalize.event import NormalizedEvent


class ExampleClassifierPlugin:
    name = "{name}"

    def classify(self, event: NormalizedEvent) -> dict | None:
        # Return None to defer to the core classifier.
        ua = (event.user_agent or "").lower()
        if "examplebot" in ua:
            return {{
                "category": "UNKNOWN AUTOMATION",
                "confidence": 0.6,
                "evidence": ["UA contains examplebot (plugin)"],
            }}
        return None
'''

_README = """# {name} BotScope plugin

Status: TEMPLATE

Register via entry point group `botscope.plugins` when packaging,
or load locally for experiments.
"""

_PYPROJECT = '''[project]
name = "botscope-plugin-{name}"
version = "0.1.0"
description = "Example BotScope plugin"
requires-python = ">=3.10"
dependencies = ["botscope>=0.1.0"]

[project.entry-points."botscope.plugins"]
{name} = "botscope_plugin_{safe}.plugin:ExampleClassifierPlugin"
'''


def create_plugin_scaffold(dest: str | Path, name: str = "example") -> Path:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    root = Path(dest) / f"botscope_plugin_{safe}"
    pkg = root / f"botscope_plugin_{safe}"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(
        '"""Example BotScope plugin package."""\n', encoding="utf-8"
    )
    (pkg / "plugin.py").write_text(
        _PLUGIN_TEMPLATE.format(name=name), encoding="utf-8"
    )
    (root / "README.md").write_text(_README.format(name=name), encoding="utf-8")
    (root / "pyproject.toml").write_text(
        _PYPROJECT.format(name=name, safe=safe), encoding="utf-8"
    )
    return root
