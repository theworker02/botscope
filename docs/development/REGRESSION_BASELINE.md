# Frozen Regression Baseline — BotScope Observatory Shell

**Frozen date:** 2026-09-18  
**Original frozen count:** **20 tests passing**  
**Current suite (confirmed):** raise with each additive release (`pytest tests -q -m "not network"`). Live network tests: `@pytest.mark.network`. Frozen floor of 20 raised, not weakened.

## Policy

Before Phase III (measurement workstation) changes:

1. The existing **PySide6 Observatory** (`botscope.gui`) is the **canonical shell**.
2. Do **not** replace it with a web UI, Electron shell, or alternate GUI framework.
3. The original **20 tests** are the frozen regression baseline. New work must keep them green.
4. New tests **raise** the floor; do not delete or weaken baseline coverage without an explicit ADR.
5. Document the current passing count in PR notes / PHASE_III progress when it changes.

## Scope of the frozen shell

Evidence-backed capabilities at freeze time:

- Observatory dashboard (shares, timeline, categories, denominator)
- Events panel + Classification Inspector
- Dataset Health, Provenance, Bot Library
- Welcome dialog, DEMO DATA banner
- Background `AnalyzeWorker`
- CLI: `botscope` / `botscope gui` launch

## Observatory v2 additions (additive; raise the floor)

| Addition | Module / UI |
|----------|-------------|
| Persistent `.bscope` save / load / history | `gui.session_io`, `history`, File menu |
| Multi-session + classifier compare | Compare tab |
| Shared query language | Events query bar, `botscope query`, `botscope.api` |
| Virtualized events model | `gui.events_model` + `QTableView` |
| Analysis Workspace | `botscope.workspace` + Workspace tab |
| Streaming snapshots + live log-tail | `botscope.live`, Live tab |

## Verification

```bash
pytest tests -q
# Expect at least the frozen baseline of 20 to remain passing.
# After v2 thickness, expect a substantially higher count — all green.
```

See also: `tests/test_regression_baseline.py`
