# Build Reproducibility — BotScope

**Date:** 2026-09-21

## Fresh machine path

```
git clone https://github.com/theworker02/botscope.git && cd botscope
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
botscope doctor
botscope demo
pytest -q
```

## Assumptions

- Stack: Python >=3.10 (Hatchling); optional PySide6 GUI
- No machine-specific absolute paths should be required.
- Cloud credentials are optional unless exercising live provider features.

## Known reproducibility limits

Documented in KNOWN_LIMITATIONS.md and project-specific diligence.
