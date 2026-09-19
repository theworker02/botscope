# Tutorial 2 — Analyze a log

Use an authorized combined/common access log:

```bash
botscope analyze path/to/access.log --output run.bscope
botscope report run.bscope --format markdown --output report.md
```

Or run `python examples/analyze_nginx.py` for the bundled demo log.
