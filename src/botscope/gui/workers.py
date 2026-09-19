"""Background workers so the Observatory UI stays responsive."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from botscope.api.analyzer import AnalysisResult, Analyzer
from botscope.capture.live import LiveCaptureConfig, iter_live_packets
from botscope.ingest.parsers import CombinedLogParser, JsonLogParser, detect_parser
from botscope.live import (
    FanInAggregator,
    LogTailConfig,
    SensorKind,
    SensorSource,
    StreamingAggregator,
    classify_live_event,
    tail_new_lines,
)
from botscope.live.pipeline import build_live_classifier
from botscope.privacy.transforms import PrivacyConfig, PrivacyTransform


class AnalyzeWorker(QThread):
    """Run Analyzer off the GUI thread."""

    finished_ok = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(
        self,
        source: Path,
        *,
        is_demo: bool = False,
        max_events: int | None = None,
        privacy: PrivacyConfig | None = None,
        use_identity_ranges: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.source = source
        self.is_demo = is_demo
        self.max_events = max_events
        self.privacy = privacy
        self.use_identity_ranges = use_identity_ranges

    def run(self) -> None:
        try:
            self.progress.emit(f"Ingesting {self.source.name}…")
            if self.use_identity_ranges:
                self.progress.emit("Loading published crawler IP ranges (cache-first)…")
            analyzer = Analyzer(
                privacy=self.privacy,
                use_identity_ranges=self.use_identity_ranges,
            )
            self.progress.emit("Classifying events…")
            result: AnalysisResult = analyzer.analyze(
                self.source,
                is_demo=self.is_demo,
                max_events=self.max_events,
            )
            detail = analyzer.identity_ranges_status.get("detail") or ""
            if detail:
                self.progress.emit(detail)
            self.progress.emit("Aggregating observatory statistics…")
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class LiveLogTailWorker(QThread):
    """Authorized live access-log tail → classify → StreamingAggregator snapshots."""

    snapshot_ready = Signal(object)
    events_batch = Signal(object)
    failed = Signal(str)
    status = Signal(str)

    def __init__(
        self,
        path: Path,
        *,
        sensor_id: str = "log-tail",
        max_hz: float = 5.0,
        poll_interval_s: float = 0.25,
        privacy: PrivacyConfig | None = None,
        fanin: FanInAggregator | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.path = Path(path)
        self.sensor_id = sensor_id
        self.max_hz = max_hz
        self.poll_interval_s = poll_interval_s
        self.privacy = privacy
        self.fanin = fanin
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            if not self.path.exists():
                self.failed.emit(f"Log path does not exist: {self.path}")
                return
            parser = detect_parser(self.path)
            if parser is None:
                parser = CombinedLogParser()
            classifier = build_live_classifier()
            privacy = PrivacyTransform(self.privacy or PrivacyConfig())
            if self.fanin is not None:
                self.fanin.register(
                    SensorSource(
                        id=self.sensor_id,
                        kind=SensorKind.LOG,
                        label=str(self.path),
                    )
                )
                aggregator = self.fanin
            else:
                aggregator = StreamingAggregator(
                    max_hz=self.max_hz,
                    source_label=str(self.path),
                    is_demo=False,
                )
            config = LogTailConfig(
                path=self.path,
                poll_interval_s=self.poll_interval_s,
                start_at_end=True,
            )
            self.status.emit(f"Tailing {self.path} (authorized)…")
            line_no = 0
            batch: list = []
            for line in tail_new_lines(config):
                if self._stop:
                    break
                line_no += 1
                if line.strip().startswith("{"):
                    event = JsonLogParser().parse_line(line, line_no=line_no)
                else:
                    event = parser.parse_line(line, line_no=line_no)
                if event is None:
                    continue
                classified = classify_live_event(
                    event,
                    classifier=classifier,
                    privacy=privacy,
                    sensor_id=self.sensor_id,
                )
                if self.fanin is not None:
                    aggregator.ingest_one(classified, sensor_id=self.sensor_id)
                else:
                    aggregator.ingest_one(classified)
                batch.append(classified)
                snap = aggregator.maybe_snapshot(is_live=True)
                if snap is not None:
                    if batch:
                        self.events_batch.emit(list(batch))
                        batch.clear()
                    self.snapshot_ready.emit(snap)
                    self.status.emit(
                        f"LIVE  {snap.total_events:,} events  "
                        f"{snap.events_per_second:.2f} evt/s (measured)"
                    )
            if batch:
                self.events_batch.emit(list(batch))
            final = aggregator.snapshot(is_live=False)
            self.snapshot_ready.emit(final)
            self.status.emit("Live tail stopped.")
        except Exception as exc:
            self.failed.emit(str(exc))


class LivePacketCaptureWorker(QThread):
    """Authorized local-interface sniff → classify → bound Observatory snapshots."""

    snapshot_ready = Signal(object)
    events_batch = Signal(object)
    failed = Signal(str)
    status = Signal(str)

    def __init__(
        self,
        interface: str,
        *,
        sensor_id: str | None = None,
        bpf_filter: str | None = None,
        max_packets: int | None = None,
        max_hz: float = 5.0,
        privacy: PrivacyConfig | None = None,
        fanin: FanInAggregator | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.interface = interface
        self.sensor_id = sensor_id or f"iface:{interface}"
        self.bpf_filter = bpf_filter
        self.max_packets = max_packets
        self.max_hz = max_hz
        self.privacy = privacy
        self.fanin = fanin
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            config = LiveCaptureConfig(
                interface=self.interface,
                bpf_filter=self.bpf_filter or None,
                max_packets=self.max_packets,
                authorized=True,
            )
            classifier = build_live_classifier()
            privacy = PrivacyTransform(self.privacy or PrivacyConfig())
            if self.fanin is not None:
                self.fanin.register(
                    SensorSource(
                        id=self.sensor_id,
                        kind=SensorKind.IFACE,
                        label=f"live:{self.interface}",
                    )
                )
                aggregator = self.fanin
            else:
                aggregator = StreamingAggregator(
                    max_hz=self.max_hz,
                    source_label=f"live:{self.interface}",
                    is_demo=False,
                )
            self.status.emit(
                f"Authorized live capture on {self.interface}"
                + (f" filter={self.bpf_filter}" if self.bpf_filter else "")
            )
            batch: list = []
            for event in iter_live_packets(config, stop_check=lambda: self._stop):
                if self._stop:
                    break
                classified = classify_live_event(
                    event,
                    classifier=classifier,
                    privacy=privacy,
                    sensor_id=self.sensor_id,
                )
                if self.fanin is not None:
                    aggregator.ingest_one(classified, sensor_id=self.sensor_id)
                else:
                    aggregator.ingest_one(classified)
                batch.append(classified)
                snap = aggregator.maybe_snapshot(is_live=True)
                if snap is not None:
                    if batch:
                        self.events_batch.emit(list(batch))
                        batch.clear()
                    self.snapshot_ready.emit(snap)
                    self.status.emit(
                        f"LIVE ● {snap.total_events:,} pkts  "
                        f"{snap.events_per_second:.2f} pkt/s (measured)"
                    )
            if batch:
                self.events_batch.emit(list(batch))
            final = aggregator.snapshot(is_live=False)
            self.snapshot_ready.emit(final)
            self.status.emit("Live packet capture stopped.")
        except Exception as exc:
            self.failed.emit(str(exc))
