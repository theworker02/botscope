# Phase II progress

Agent 2 expansion track. Labels match code on disk.

| Workstream | Status | Notes |
|------------|--------|-------|
| A Docs + GitHub community | PARTIAL → largely filled | `.github/` present; core status docs present; tutorials/guides still expanding |
| B Provenance / quality / compare / research | IMPLEMENTED | Modules + tests |
| C Plugin SDK / diagnostics / audit | IMPLEMENTED / PARTIAL | SDK + doctor done; repo_audit pending polish |
| D Testing | IMPLEMENTED | Agent 2 test packages under `tests/` |
| E Integration with Agent 1 | PARTIAL | CLI uses Analyzer/SessionStore; no core overwrites |

## Empty-folder remediation (this turn)

Previously empty packages under `src/botscope/` (`cli`, `demo`, `gui`, `notebook`, `plugins/sdk`) and empty `examples/`, `datasets/demo`, test dirs were filled with real modules, runnable examples, and tests. Additional packages `capture`, `enrich`, `behavior`, `flows`, `estimation`, `datasets` added with honest PARTIAL/EXPERIMENTAL/RESEARCH status.
