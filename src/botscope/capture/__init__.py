"""Authorized capture helpers.

Status: PARTIAL — offline PCAP ingest IMPLEMENTED; live sniff requires scapy + auth.
"""

from botscope.capture.core import CapturePlan, capture_status, scapy_available
from botscope.capture.live import (
    LiveCaptureConfig,
    iter_live_packets,
    list_interfaces,
    live_capture_status,
)

__all__ = [
    "CapturePlan",
    "LiveCaptureConfig",
    "capture_status",
    "iter_live_packets",
    "list_interfaces",
    "live_capture_status",
    "scapy_available",
]
