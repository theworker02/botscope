"""Minimal example classifier plugin used by examples/plugin_example."""

from __future__ import annotations

from botscope.normalize.event import NormalizedEvent


class ExampleClassifierPlugin:
    name = "example_plugin"

    def classify(self, event: NormalizedEvent) -> dict | None:
        ua = (event.user_agent or "").lower()
        if "examplebot" in ua:
            return {
                "category": "UNKNOWN AUTOMATION",
                "confidence": 0.6,
                "evidence": ["UA contains examplebot (example plugin)"],
            }
        return None
