#!/usr/bin/env python3
"""Analyze the bundled nginx-style demo access log via the public Analyzer API."""

from __future__ import annotations

from botscope.api import Analyzer
from botscope.demo import DEMO_NOTICE, ensure_demo_log


def main() -> None:
    print(DEMO_NOTICE)
    path = ensure_demo_log()
    result = Analyzer().analyze(path, is_demo=True)
    print(f"events: {len(result.events)}")
    print(f"automated: {result.automation_fraction}")
    print(f"human-likely: {result.human_fraction}")
    print(f"unknown: {result.unknown_fraction}")
    print("categories:", result.stats.by_category)


if __name__ == "__main__":
    main()
