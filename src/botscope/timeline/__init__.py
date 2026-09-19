"""Multi-resolution timeline bucketing.

Status: IMPLEMENTED

Used by Observatory charts and StreamingAggregator. Buckets are derived
from real event timestamps — never fabricated.
"""

from __future__ import annotations

from botscope.timeline.bucket import (
    BucketResolution,
    TimelineBucket,
    TimelineSeries,
    auto_resolution,
    bucket_events,
)

__all__ = [
    "BucketResolution",
    "TimelineBucket",
    "TimelineSeries",
    "auto_resolution",
    "bucket_events",
]
