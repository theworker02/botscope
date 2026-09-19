#!/usr/bin/env python3
"""Show how a custom callable classifier can be compared against the core engine."""

from __future__ import annotations

import json

from botscope.api import Analyzer
from botscope.classify.result import ClassificationResult
from botscope.classify.taxonomy import BotCategory
from botscope.compare import compare_classifiers
from botscope.demo import DEMO_NOTICE, ensure_demo_log
from botscope.normalize.event import NormalizedEvent


def ua_contains_bot(event: NormalizedEvent) -> ClassificationResult:
    ua = (event.user_agent or "").lower()
    if "bot" in ua or "crawler" in ua:
        return ClassificationResult(
            category=BotCategory.UNKNOWN_AUTOMATION,
            confidence=0.55,
        )
    return ClassificationResult(category=BotCategory.UNKNOWN, confidence=0.2)


def main() -> None:
    print(DEMO_NOTICE)
    events = Analyzer().analyze(ensure_demo_log(), is_demo=True).events
    result = compare_classifiers(events, left=Analyzer().classifier, right=ua_contains_bot)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
