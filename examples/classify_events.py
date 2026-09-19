#!/usr/bin/env python3
"""Classify individual normalized events and print evidence."""

from __future__ import annotations

from botscope.api import Analyzer
from botscope.demo import DEMO_NOTICE, iter_demo_events


def main() -> None:
    print(DEMO_NOTICE)
    analyzer = Analyzer()
    for i, event in enumerate(iter_demo_events()):
        if i >= 5:
            break
        result = analyzer.classify_event(event)
        print("---")
        print("ua:", event.user_agent)
        print("category:", result.category.value)
        print("confidence:", result.confidence)
        for ev in result.evidence[:3]:
            print(f"  [{ev.polarity}] {ev.statement}")


if __name__ == "__main__":
    main()
