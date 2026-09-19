# Tutorial 3 — Provenance and quality

```bash
python examples/inspect_provenance.py
```

In Python:

```python
from botscope.quality import build_scorecard
card = build_scorecard(events)
print(card.to_dict()["policy"])  # no single misleading %
```
