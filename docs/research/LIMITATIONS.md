# Limitations

Status: IMPLEMENTED (documented constraints)

- Single-site/sensor corpora do not imply Internet-wide prevalence. Local Observatory KPIs stay **dataset-scoped**; Global Observatory census views and any gated Internet headline are separate surfaces with their own evidence rules.
- User-Agent strings are spoofable; verified identity ranges reduce but do not eliminate spoofing.
- Confidence is not a calibrated probability (unless an explicit calibration report with labels is produced).
- Offline PCAP ingest and authorized live capture **are implemented** but remain capability-gated: classic pcap via stdlib; pcapng via optional `scapy`; live sniff needs `botscope[capture]`, explicit authorization, and OS permissions. Treat edge cases as PARTIAL, not “missing entirely.”
- Demo / synthetic data must not be published as observational science (DEMO DATA banner / `--demo`).
- Optional enrichment network lookups and Cloudflare Radar are **OFF by default**.
- Network contribution to any shared panel is **OFF by default**.
- Federated public source panels can be stale, incomplete, or operator-specific; provenance badges matter.
- ML classifier paths never override verified identity and are not a prevalence claim.
