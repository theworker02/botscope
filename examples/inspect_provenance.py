#!/usr/bin/env python3
"""Inspect measurement provenance for a demo analysis corpus."""

from __future__ import annotations

import json

from botscope.api import Analyzer
from botscope.demo import DEMO_NOTICE, ensure_demo_log
from botscope.provenance import claim_safe_totals, inspect_event, summarize_corpus


def main() -> None:
    print(DEMO_NOTICE)
    result = Analyzer().analyze(ensure_demo_log(), is_demo=True)
    summary = summarize_corpus(result.events)
    print(json.dumps(summary.to_dict(), indent=2))
    print("--- claim-safe totals ---")
    print(json.dumps(claim_safe_totals(result.events), indent=2))
    if result.events:
        print("--- first event field provenance (sample) ---")
        report = inspect_event(result.events[0])
        present = [f.field for f in report.fields if f.present]
        print("event_level:", report.event_level.value)
        print("present_fields:", present[:12])


if __name__ == "__main__":
    main()
