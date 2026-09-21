# Test Evidence — BotScope

**Date:** 2026-09-21

## Commands run

```
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
botscope doctor
botscope demo
pytest -q
```

## Results

| Check | Status | Detail |
|-------|--------|--------|
| Install | VERIFIED | botscope 2.0.0 |
| doctor | VERIFIED | core ok |
| demo | VERIFIED | DEMO DATA; 20 events |
| pytest | VERIFIED | **131 passed, 3 skipped** |
