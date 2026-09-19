# File Ownership — BotScope

**Status:** IMPLEMENTED (process document)  
**Companion:** [PARALLEL_WORK_LEDGER.md](PARALLEL_WORK_LEDGER.md)

## Legend

- **A1** — Agent 1 (Core Builder): do not rewrite casually
- **A2** — Agent 2 (Phase II Expansion): preferred owner for new isolated work
- **Shared** — coordinate; re-read before edit; merge intentionally

## Directory ownership

| Path | Owner | Edit policy |
|------|-------|-------------|
| `src/botscope/api/` | A1 | Avoid unless fixing integration bug |
| `src/botscope/classify/` | A1 | No architecture changes |
| `src/botscope/identity/` | A1 | Avoid |
| `src/botscope/ingest/` | A1 | Avoid |
| `src/botscope/normalize/` | A1 | Avoid; extend via `provenance/` |
| `src/botscope/storage/` | A1 | Avoid schema breaks; A2 may read sessions |
| `src/botscope/statistics/` | A1 | Avoid |
| `src/botscope/reports/` | A1 | Extend carefully; prefer new helpers |
| `src/botscope/signatures/` | A1 | Avoid |
| `src/botscope/privacy/` | A1 | Avoid |
| `src/botscope/network/` | A1 | Avoid; keep OFF-by-default |
| `src/botscope/native.py` | A1 | Avoid |
| `src/botscope/plugins/system.py` | A1 | Avoid |
| `src/botscope/plugins/sdk/` | A2 | Own |
| `src/botscope/provenance/` | A2 | Own |
| `src/botscope/quality/` | A2 | Own |
| `src/botscope/compare/` | A2 | Own |
| `src/botscope/research/` | A2 | Own |
| `src/botscope/sources/` | A2 | Own |
| `src/botscope/query/` | A2 | Own |
| `src/botscope/annotations/` | A2 | Own |
| `src/botscope/notebook/` | A2 | Own |
| `src/botscope/diagnostics/` | A2 | Own |
| `src/botscope/capabilities/` | A2 | Own |
| `src/botscope/botcard/` | A2 | Own |
| `src/botscope/manifests/` | A2 | Own |
| `src/botscope/cli/main.py` | Shared | Thin dispatcher |
| `src/botscope/cli/*_cmd.py` (A2 cmds) | A2 | Own |
| `src/botscope/cli/*_cmd.py` (analyze/demo/gui) | A1 preferred | A2 may fill if missing |
| `docs/` | A2 | Stewardship |
| `.github/` | A2 | Own |
| `tests/` for A2 modules | A2 | Own |
| `examples/`, `scripts/` | A2 | Own |
| `pyproject.toml` | Shared | Preserve package name & entry point |
| `README.md` | Shared | Concise; deep material in docs |

## Before touching a Shared or A1 file

1. Re-read the file from disk (Agent 1 may have changed it).
2. Diff mentally against last known content.
3. Apply the smallest merge that preserves both intents.
4. Update this ledger if ownership shifts.
