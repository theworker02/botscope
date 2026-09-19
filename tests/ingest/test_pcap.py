"""PCAP ingest and live capture authorization tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from botscope.api.analyzer import Analyzer
from botscope.capture.live import LiveCaptureConfig, iter_live_packets
from botscope.ingest.pcap import iter_pcap_events, write_minimal_ipv4_pcap
from botscope.normalize.event import SourceType


def test_classic_pcap_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "sample.pcap"
    write_minimal_ipv4_pcap(
        path,
        [
            {"src": "203.0.113.10", "dst": "198.51.100.2", "sport": 443, "dport": 80},
            {"src": "203.0.113.11", "dst": "198.51.100.2", "sport": 444, "dport": 443},
        ],
    )
    events = list(iter_pcap_events(path))
    assert len(events) == 2
    assert events[0].source_type == SourceType.PCAP
    assert events[0].src_address == "203.0.113.10"
    assert events[0].dst_port == 80
    assert events[0].extras.get("payload_excluded") is True


def test_analyzer_accepts_pcap(tmp_path: Path) -> None:
    path = tmp_path / "flow.pcap"
    write_minimal_ipv4_pcap(path, [{"src": "1.2.3.4", "dst": "5.6.7.8", "dport": 80}])
    result = Analyzer().analyze(path)
    assert len(result.events) == 1
    assert result.events[0].source_type == SourceType.PCAP


def test_live_capture_requires_authorization() -> None:
    cfg = LiveCaptureConfig(interface="lo", authorized=False)
    with pytest.raises(PermissionError):
        next(iter_live_packets(cfg))
