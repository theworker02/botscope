"""Authorized live ingest foundation.

Status: IMPLEMENTED — log-tail, offline PCAP, live sniff (scapy+auth),
persist, multi-sensor fan-in, and threshold alerts.

Decouples ingestion rate from GUI refresh via bounded ObservatorySnapshot
publication (few Hz). Network contribution remains OFF by default.
"""

from __future__ import annotations

from botscope.live.aggregator import ObservatorySnapshot, StreamingAggregator
from botscope.live.alerts import (
    Alert,
    AlertEngine,
    AlertRule,
    AlertSeverity,
    default_alert_rules,
)
from botscope.live.fanin import FanInAggregator, SensorKind, SensorSource
from botscope.live.log_tail import LogTailConfig, tail_new_lines
from botscope.live.persist import LiveSessionWriter, suggest_live_session_path
from botscope.live.pipeline import build_live_classifier, classify_live_event

__all__ = [
    "ObservatorySnapshot",
    "StreamingAggregator",
    "LogTailConfig",
    "tail_new_lines",
    "LiveSessionWriter",
    "suggest_live_session_path",
    "FanInAggregator",
    "SensorKind",
    "SensorSource",
    "Alert",
    "AlertEngine",
    "AlertRule",
    "AlertSeverity",
    "default_alert_rules",
    "build_live_classifier",
    "classify_live_event",
]
