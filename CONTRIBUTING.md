# Contributing

Thanks for helping improve BotScope.

## Development setup

```bash
pip install -e ".[dev]"
pytest
ruff check src tests scripts
```

## Guidelines

1. Prefer small, focused PRs.
2. Do not invent benchmarks, DOIs, or Internet-wide prevalence claims.
3. Keep network contribution **OFF by default**.
4. Use honest status labels in docs: IMPLEMENTED / PARTIAL / EXPERIMENTAL / PLANNED / RESEARCH / NOT IMPLEMENTED.
5. UNKNOWN must remain a valid classification outcome.
6. Do not commit secrets, raw PII logs, or unauthorized capture data.
7. When working in parallel, re-read shared files before editing — see `docs/development/FILE_OWNERSHIP.md`.

## Code style

- Python 3.10+
- Ruff for lint
- Pytest for tests
- Conventional commits preferred (`feat`, `fix`, `docs`, `test`, `chore`)

## Security issues

See [SECURITY.md](SECURITY.md) — do not file public issues for vulnerabilities.
