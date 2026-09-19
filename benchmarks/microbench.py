"""Runnable microbenchmarks with receipt schema.

Never invent timings for docs. Run this module and record the receipt JSON.

Usage:
  python -m benchmarks.microbench
  python benchmarks/microbench.py --output receipt.json
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class BenchReceipt:
    name: str
    iterations: int
    elapsed_s: float
    per_iter_ms: float
    note: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _timeit(name: str, fn: Callable[[], None], *, iterations: int, note: str) -> BenchReceipt:
    # Warmup
    fn()
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    return BenchReceipt(
        name=name,
        iterations=iterations,
        elapsed_s=elapsed,
        per_iter_ms=(elapsed / iterations) * 1000.0,
        note=note,
    )


def run_suite() -> list[BenchReceipt]:
    from botscope.demo import ensure_demo_log, iter_demo_events
    from botscope.query import filter_events, parse_simple_query
    from botscope.timeline import bucket_events
    from botscope.live import StreamingAggregator

    events = list(iter_demo_events())
    receipts: list[BenchReceipt] = []

    def parse_query() -> None:
        parse_simple_query('classification eq "AI CRAWLER" AND confidence gte 0.5')

    receipts.append(
        _timeit("parse_simple_query", parse_query, iterations=500, note="query parse only")
    )

    preds = parse_simple_query('user_agent icontains bot')

    def run_filter() -> None:
        list(filter_events(events, preds))

    receipts.append(
        _timeit(
            "filter_events_demo",
            run_filter,
            iterations=50,
            note=f"filter {len(events)} demo events",
        )
    )

    def run_buckets() -> None:
        bucket_events(events)

    receipts.append(
        _timeit("bucket_events_demo", run_buckets, iterations=50, note="timeline bucketing")
    )

    def run_agg() -> None:
        agg = StreamingAggregator(max_hz=1000.0)
        agg.ingest(events)
        agg.snapshot()

    receipts.append(
        _timeit(
            "streaming_aggregator_demo",
            run_agg,
            iterations=20,
            note="ingest + snapshot over demo corpus",
        )
    )

    # Touch demo log path so receipt documents corpus provenance
    ensure_demo_log()
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser(description="BotScope microbenchmarks")
    parser.add_argument("--output", type=Path, default=None, help="Write receipt JSON")
    args = parser.parse_args()
    receipts = run_suite()
    payload = {
        "suite": "botscope_microbench",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "receipts": [r.to_dict() for r in receipts],
        "disclaimer": "Measured on this machine only — do not treat as product SLAs.",
    }
    text = json.dumps(payload, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
