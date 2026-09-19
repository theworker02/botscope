"""Authorized capture helpers.

Status: PARTIAL — offline PCAP available; live sniff needs scapy + explicit auth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapturePlan:
    """Describe an authorized capture without performing network probing."""

    interface: str | None = None
    bpf_filter: str | None = None
    max_packets: int | None = None
    note: str = (
        "Capture must be authorized. BotScope does not scan third-party networks."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "interface": self.interface,
            "bpf_filter": self.bpf_filter,
            "max_packets": self.max_packets,
            "status": "PARTIAL",
            "note": self.note,
            "live_capture": "AVAILABLE" if scapy_available() else "NOT_INSTALLED",
            "offline_pcap": "AVAILABLE (classic pcap via stdlib; pcapng via scapy)",
            "policy": "Explicit authorization required for live sniffing.",
        }


def scapy_available() -> bool:
    try:
        import scapy  # noqa: F401

        return True
    except ImportError:
        return False


def capture_status() -> dict[str, Any]:
    return {
        "scapy_available": scapy_available(),
        "live_capture": "AVAILABLE" if scapy_available() else "NOT_INSTALLED",
        "offline_pcap": "AVAILABLE",
        "default": "offline log / pcap ingest",
        "policy": "No unauthorized probing",
    }
