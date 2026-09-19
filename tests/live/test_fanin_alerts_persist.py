"""Live persist, fan-in, and alert tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from botscope.live import (
    AlertEngine,
    AlertRule,
    AlertSeverity,
    FanInAggregator,
    LiveSessionWriter,
    SensorKind,
    SensorSource,
    StreamingAggregator,
    default_alert_rules,
)
from botscope.normalize.event import NormalizedEvent, SourceType


def _evt(cat: str = "AI CRAWLER", sensor: str | None = None) -> NormalizedEvent:
    return NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        source_type=SourceType.WEB_LOG,
        classification=cat,
        confidence=0.7,
        bytes_out=100,
        sensor_id=sensor,
        src_address="203.0.113.10",
    )


def test_live_session_writer_append(tmp_path: Path) -> None:
    path = tmp_path / "live.bscope"
    writer = LiveSessionWriter(path, source_label="test")
    sid = writer.open()
    assert sid
    n = writer.append([_evt(), _evt("HUMAN-LIKELY")])
    assert n == 2
    writer.flush()
    root = writer.close()
    assert root is not None
    assert (root / "events.jsonl").exists()
    lines = (root / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_fanin_tags_sensors() -> None:
    fan = FanInAggregator(max_hz=100.0)
    fan.register(SensorSource(id="a", kind=SensorKind.LOG, label="log-a"))
    fan.register(SensorSource(id="b", kind=SensorKind.IFACE, label="iface-b"))
    fan.ingest_one(_evt(sensor=None), sensor_id="a")
    fan.ingest_one(_evt("UNKNOWN"), sensor_id="b")
    snap = fan.snapshot()
    assert snap.total_events == 2
    assert fan.sensor_counts() == {"a": 1, "b": 1}
    assert "Sensors:" in snap.note


def test_alert_engine_threshold() -> None:
    engine = AlertEngine(
        rules=[
            AlertRule(
                id="auto",
                name="High auto",
                metric="automated_share",
                op=">",
                threshold=0.5,
                min_events=2,
                severity=AlertSeverity.WARNING,
            )
        ]
    )
    agg = StreamingAggregator(max_hz=100.0)
    for _ in range(5):
        agg.ingest_one(_evt())
    snap = agg.snapshot()
    alerts = engine.evaluate(snap)
    assert alerts
    assert alerts[0].rule_id == "auto"
    # Edge trigger: second evaluate should not re-fire
    assert engine.evaluate(snap) == []


def test_default_alert_rules_nonempty() -> None:
    assert default_alert_rules()
