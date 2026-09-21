# Buyer Demo — BotScope

**Target:** fresh machine → clone → install → run → verify (≈10–15 minutes where realistic).

## Exact commands

```bash
git clone https://github.com/theworker02/botscope.git && cd botscope
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
botscope doctor
botscope demo
pytest -q
```

## Expected results

- Commands exit 0 (or documented skip for optional live-cloud steps).
- No secrets required for the minimal path.
- See TEST_EVIDENCE.md for recorded exit codes from this program’s verification runs.

## Out of scope for minimal demo

- Live production cloud credentials
- Shipping malware / real vehicle bus hardware (OpenDashCAN)
- Paid API quotas
