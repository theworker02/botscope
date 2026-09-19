"""Architecture note: Live Observatory refresh path.

```
Authorized log file
      │
      ▼
LiveLogTailWorker (QThread)
  parse line → privacy → classify
      │
      ├──► SessionStore / in-memory events (analytical)
      │
      ▼
StreamingAggregator (botscope.live)
  counters + timeline buckets
      │  rate-limited (e.g. 4–10 Hz)
      ▼
ObservatorySnapshot  ──snapshot_ready──►  ObservatoryPanel.apply_snapshot()
                                         Events panel refreshed on batches
```

GUI refresh is intentionally decoupled from per-event ingest rate.
Sensor ● LIVE only while the authorized worker is running; evt/s is measured.
"""
