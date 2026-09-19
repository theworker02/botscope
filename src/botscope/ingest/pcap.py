"""PCAP / PCAPNG ingest — metadata-oriented, no payload collection by default.

Status: IMPLEMENTED (classic PCAP stdlib) / PARTIAL (PCAPNG prefers scapy when present)

Authorized offline analysis only. Does not open live sockets.
"""

from __future__ import annotations

import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from botscope.normalize.event import NormalizedEvent, SourceType

# Classic pcap magic numbers
MAGIC_LE = 0xA1B2C3D4
MAGIC_BE = 0xD4C3B2A1
MAGIC_NS_LE = 0xA1B23C4D
MAGIC_NS_BE = 0x4D3CB2A1

LINKTYPE_ETHERNET = 1
ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_IPV6 = 0x86DD
PROTO_TCP = 6
PROTO_UDP = 17
PROTO_ICMP = 1


class PcapParseError(ValueError):
    """Raised for malformed or unsupported capture files."""


def _u16(data: bytes, off: int, *, be: bool) -> int:
    fmt = ">H" if be else "<H"
    return struct.unpack_from(fmt, data, off)[0]


def _u32(data: bytes, off: int, *, be: bool) -> int:
    fmt = ">I" if be else "<I"
    return struct.unpack_from(fmt, data, off)[0]


def _parse_ipv4(packet: bytes, offset: int) -> dict | None:
    if len(packet) < offset + 20:
        return None
    vihl = packet[offset]
    version = vihl >> 4
    ihl = (vihl & 0x0F) * 4
    if version != 4 or ihl < 20 or len(packet) < offset + ihl:
        return None
    total_len = struct.unpack_from("!H", packet, offset + 2)[0]
    proto = packet[offset + 9]
    src = ".".join(str(b) for b in packet[offset + 12 : offset + 16])
    dst = ".".join(str(b) for b in packet[offset + 16 : offset + 20])
    payload_off = offset + ihl
    src_port = dst_port = None
    transport = None
    if proto == PROTO_TCP and len(packet) >= payload_off + 4:
        src_port, dst_port = struct.unpack_from("!HH", packet, payload_off)
        transport = "tcp"
    elif proto == PROTO_UDP and len(packet) >= payload_off + 4:
        src_port, dst_port = struct.unpack_from("!HH", packet, payload_off)
        transport = "udp"
    elif proto == PROTO_ICMP:
        transport = "icmp"
    return {
        "protocol": "IP",
        "transport": transport,
        "src_address": src,
        "dst_address": dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "bytes_in": max(0, min(total_len, len(packet) - offset)),
    }


def _parse_ethernet_frame(frame: bytes) -> dict | None:
    if len(frame) < 14:
        return None
    ethertype = struct.unpack_from("!H", frame, 12)[0]
    if ethertype == ETHERTYPE_IPV4:
        return _parse_ipv4(frame, 14)
    if ethertype == 0x8100 and len(frame) >= 18:  # 802.1Q
        ethertype = struct.unpack_from("!H", frame, 16)[0]
        if ethertype == ETHERTYPE_IPV4:
            return _parse_ipv4(frame, 18)
    # Raw IP (some captures)
    if frame and (frame[0] >> 4) == 4:
        return _parse_ipv4(frame, 0)
    return {
        "protocol": f"ethertype-0x{ethertype:04x}",
        "transport": None,
        "src_address": None,
        "dst_address": None,
        "src_port": None,
        "dst_port": None,
        "bytes_in": len(frame),
    }


def iter_pcap_events(
    path: str | Path,
    *,
    max_packets: int | None = 500_000,
    max_bytes: int = 512 * 1024 * 1024,
) -> Iterator[NormalizedEvent]:
    """Stream NormalizedEvent records from a classic pcap file (no payloads stored)."""
    path = Path(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise PcapParseError(
            f"Capture exceeds safety limit ({size} > {max_bytes} bytes). "
            "Raise max_bytes only for authorized large imports."
        )
    with path.open("rb") as handle:
        hdr = handle.read(24)
        if len(hdr) < 24:
            raise PcapParseError("File too small to be a pcap")
        magic = struct.unpack_from("<I", hdr, 0)[0]
        if magic in (MAGIC_LE, MAGIC_NS_LE):
            be = False
            ns = magic == MAGIC_NS_LE
        elif magic in (MAGIC_BE, MAGIC_NS_BE):
            be = True
            ns = magic == MAGIC_NS_BE
            magic = struct.unpack_from(">I", hdr, 0)[0]
        else:
            # Maybe pcapng — try scapy fallback
            yield from _iter_via_scapy(path, max_packets=max_packets)
            return

        linktype = _u32(hdr, 20, be=be)
        count = 0
        while True:
            ph = handle.read(16)
            if len(ph) < 16:
                break
            ts_sec = _u32(ph, 0, be=be)
            ts_sub = _u32(ph, 4, be=be)
            incl_len = _u32(ph, 8, be=be)
            _orig_len = _u32(ph, 12, be=be)
            if incl_len > 16 * 1024 * 1024:
                raise PcapParseError(f"Implausible packet length: {incl_len}")
            data = handle.read(incl_len)
            if len(data) < incl_len:
                break
            if ns:
                micros = ts_sub // 1000
            else:
                micros = ts_sub
            ts = datetime.fromtimestamp(ts_sec + micros / 1_000_000.0, tz=timezone.utc)
            fields: dict = {
                "protocol": "unknown",
                "transport": None,
                "src_address": None,
                "dst_address": None,
                "src_port": None,
                "dst_port": None,
                "bytes_in": incl_len,
            }
            if linktype == LINKTYPE_ETHERNET:
                parsed = _parse_ethernet_frame(data)
                if parsed:
                    fields.update(parsed)
            elif linktype == 101:  # raw IP
                parsed = _parse_ipv4(data, 0)
                if parsed:
                    fields.update(parsed)
            count += 1
            yield NormalizedEvent(
                timestamp=ts,
                source_type=SourceType.PCAP,
                protocol=fields.get("protocol"),
                transport=fields.get("transport"),
                src_address=fields.get("src_address"),
                dst_address=fields.get("dst_address"),
                src_port=fields.get("src_port"),
                dst_port=fields.get("dst_port"),
                bytes_in=fields.get("bytes_in"),
                bytes_out=None,
                raw_ref=f"pcap:{path.name}:{count}",
                extras={"linktype": linktype, "payload_excluded": True},
            )
            if max_packets is not None and count >= max_packets:
                break


def _iter_via_scapy(
    path: Path, *, max_packets: int | None
) -> Iterator[NormalizedEvent]:
    try:
        from scapy.all import PcapReader  # type: ignore
        from scapy.layers.inet import IP, TCP, UDP  # type: ignore
    except ImportError as exc:
        raise PcapParseError(
            "File does not look like classic pcap, and scapy is not installed "
            "for PCAPNG/fallback. Install with: pip install 'botscope[capture]'"
        ) from exc

    count = 0
    with PcapReader(str(path)) as reader:
        for pkt in reader:
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
                raw_ref=f"pcapng:{path.name}:{count}",
                extras={"payload_excluded": True, "backend": "scapy"},
            )
            if max_packets is not None and count >= max_packets:
                break


def is_pcap_path(path: str | Path) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in {".pcap", ".pcapng", ".cap"}


def write_minimal_ipv4_pcap(path: str | Path, packets: list[dict]) -> Path:
    """Test helper: write a tiny Ethernet/IPv4/TCP pcap (little-endian)."""
    path = Path(path)
    # Global header LE
    gh = struct.pack("<IHHIIII", MAGIC_LE, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET)
    chunks = [gh]
    for i, spec in enumerate(packets):
        src = bytes(int(x) for x in spec.get("src", "10.0.0.1").split("."))
        dst = bytes(int(x) for x in spec.get("dst", "10.0.0.2").split("."))
        sport = int(spec.get("sport", 12345))
        dport = int(spec.get("dport", 80))
        ts = int(spec.get("ts", 1_700_000_000 + i))
        # Ethernet
        eth = b"\x00" * 6 + b"\x11" * 6 + struct.pack("!H", ETHERTYPE_IPV4)
        # IPv4 header (20) + TCP (20)
        tcp = struct.pack("!HHIIBBHHH", sport, dport, 0, 0, 5 << 4, 0x02, 8192, 0, 0)
        total = 20 + len(tcp)
        ip = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            total,
            0,
            0,
            64,
            PROTO_TCP,
            0,
            src,
            dst,
        )
        frame = eth + ip + tcp
        ph = struct.pack("<IIII", ts, 0, len(frame), len(frame))
        chunks.append(ph + frame)
    path.write_bytes(b"".join(chunks))
    return path
