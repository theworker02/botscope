"""Authorized live packet capture (optional scapy).

Status: PARTIAL — requires botscope[capture], explicit authorization, and
platform permissions. Never probes third-party networks; sniffs only the
user-selected local interface with an optional BPF filter.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterator

from botscope.capture.core import CapturePlan, capture_status, scapy_available
from botscope.normalize.event import NormalizedEvent, SourceType


@dataclass
class LiveCaptureConfig:
    """User-authorized live capture parameters."""

    interface: str
    bpf_filter: str | None = None
    max_packets: int | None = None
    max_seconds: float | None = None
    authorized: bool = False  # MUST be True to start

    def to_plan(self) -> CapturePlan:
        return CapturePlan(
            interface=self.interface,
            bpf_filter=self.bpf_filter,
            max_packets=self.max_packets,
            note=(
                "Authorized local interface capture only. "
                "BotScope does not scan third-party networks."
            ),
        )


def list_interfaces() -> list[dict[str, Any]]:
    """List local interfaces when scapy is available."""
    if not scapy_available():
        return []
    try:
        from scapy.all import get_if_list  # type: ignore

        return [{"name": name} for name in get_if_list()]
    except Exception:  # noqa: BLE001
        return []


def iter_live_packets(
    config: LiveCaptureConfig,
    *,
    stop_check: Callable[[], bool] | None = None,
) -> Iterator[NormalizedEvent]:
    """Yield normalized events from an authorized local sniff session.

    Raises PermissionError if ``authorized`` is False.
    Raises RuntimeError if scapy is not installed.
    """
    if not config.authorized:
        raise PermissionError(
            "Live packet capture requires explicit authorization "
            "(LiveCaptureConfig.authorized=True)."
        )
    if not scapy_available():
        raise RuntimeError(
            "Live packet capture requires scapy. Install with: pip install 'botscope[capture]'"
        )

    from scapy.all import IP, TCP, UDP, sniff  # type: ignore

    started = time.monotonic()
    count = 0

    def _stop_filter(_pkt: Any) -> bool:
        nonlocal count
        if stop_check and stop_check():
            return True
        if config.max_packets is not None and count >= config.max_packets:
            return True
        if config.max_seconds is not None and (time.monotonic() - started) >= config.max_seconds:
            return True
        return False

    # Use sniff in small batches so we can convert and respect stop_check.
    while True:
        if stop_check and stop_check():
            break
        if config.max_packets is not None and count >= config.max_packets:
            break
        if config.max_seconds is not None and (time.monotonic() - started) >= config.max_seconds:
            break
        remaining = None
        if config.max_packets is not None:
            remaining = max(1, config.max_packets - count)
        batch_size = min(32, remaining) if remaining else 32
        timeout = 0.5
        if config.max_seconds is not None:
            timeout = min(timeout, max(0.1, config.max_seconds - (time.monotonic() - started)))

        pkts = sniff(
            iface=config.interface,
            filter=config.bpf_filter or None,
            count=batch_size,
            timeout=timeout,
            store=True,
            stop_filter=_stop_filter if (config.max_packets or config.max_seconds) else None,
        )
        if not pkts:
            if stop_check and stop_check():
                break
            if config.max_seconds is not None and (time.monotonic() - started) >= config.max_seconds:
                break
            continue
        for pkt in pkts:
            count += 1
            ts = datetime.fromtimestamp(float(pkt.time), tz=timezone.utc)
            src = dst = None
            sport = dport = None
            transport = None
            protocol = "packet"
            if IP in pkt:
                ip = pkt[IP]
                src, dst = ip.src, ip.dst
                protocol = "IP"
                if TCP in pkt:
                    transport = "tcp"
                    sport, dport = int(pkt[TCP].sport), int(pkt[TCP].dport)
                elif UDP in pkt:
                    transport = "udp"
                    sport, dport = int(pkt[UDP].sport), int(pkt[UDP].dport)
            yield NormalizedEvent(
                timestamp=ts,
                source_type=SourceType.PCAP,
                protocol=protocol,
                transport=transport,
                src_address=src,
                dst_address=dst,
                src_port=sport,
                dst_port=dport,
                bytes_in=len(pkt),
                raw_ref=f"live:{config.interface}:{count}",
                extras={
                    "payload_excluded": True,
                    "interface": config.interface,
                    "bpf_filter": config.bpf_filter,
                    "live": True,
                },
            )
            if config.max_packets is not None and count >= config.max_packets:
                return


def live_capture_status() -> dict[str, Any]:
    status = capture_status()
    status["interfaces"] = list_interfaces()
    status["policy"] = (
        "Explicit authorization required. Local interface only. "
        "No unauthorized probing. Payload bytes are not retained as content."
    )
    return status
