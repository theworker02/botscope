# Capture & PCAP

**Status:** IMPLEMENTED (authorized local sources only)

## Offline PCAP

```bash
botscope analyze traffic.pcap
# or open via GUI Live → Browse PCAP / File → Open
```

- Classic `.pcap` parsed with the stdlib (no scapy required)
- `.pcapng` uses scapy when installed (`pip install 'botscope[capture]'`)
- Metadata only — payloads excluded by default
- Events become `source_type=pcap` and flow through classify → Observatory

## Live log tail

GUI **Live** tab → authorize → Start live log tail. Bound snapshots feed the Observatory (not one GUI update per line). Batches append to a live `.bscope`.

```bash
botscope live-tail access.log --authorize --max-lines 200 --output live.bscope
```

## Live interface sniff

Requires:

```bash
pip install 'botscope[capture]'
```

plus OS capture permissions and an explicit authorization checkbox / `--authorize`.

```bash
botscope capture --list-interfaces
botscope capture --iface eth0 --authorize --max-packets 100 --output live_cap.bscope
```

BotScope sniffs only the **user-selected local interface** with an optional BPF filter. It does not scan third-party networks.

## Multi-sensor + alerts

Start log-tail and interface capture together in the GUI — events fan into one Observatory stream with `sensor_id` tags. Threshold alerts (automated share, unknown share, event-rate burst) appear in the Live panel.

## Policy

- Authorization required
- No silent telemetry / Network contribution OFF by default
- Sensor ● LIVE only while a feed is actually running
- Rates are measured from the stream — never placeholders
