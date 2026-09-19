# Measurement methodology (research companion)

This document expands the scientific posture of BotScope measurements.

## What BotScope measures

BotScope classifies **authorized sensor observations** (typically web access logs)
into taxonomy categories using evidence-backed heuristics. Aggregates over a
session are **CLASSIFIED** shares for that source only.

## What BotScope does not claim

- IP geolocation ≠ person location (`botscope.geo` caveat).
- User-Agent strings alone do not verify bot identity.
- Confidence scores in v0.1 are heuristics — use `botscope.calibration` with
  labeled fixtures to quantify miscalibration (Brier / ECE).
- Session deltas (`botscope.compare`) are descriptive, not causal.

## Evaluation

Labeled fixtures live under `datasets/fixtures/`. Run:

```python
from botscope.eval import evaluate_labels
# y_true from fixture labels; y_pred from classifier outputs
```

## Companion modules

| Module | Role |
|--------|------|
| `botscope.timeline` | Multi-resolution bucketing |
| `botscope.calibration` | Reliability diagrams / ECE / Brier |
| `botscope.eval` | Precision / recall / F1 |
| `botscope.live` | Authorized live ingest + snapshots |
| `botscope.workspace` | Analysis view-state persistence |

See also: `docs/research/METHODOLOGY.md`, `docs/research/LIMITATIONS.md`.
