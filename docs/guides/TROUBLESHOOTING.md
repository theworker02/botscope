# Troubleshooting

| Symptom | Check |
|---------|-------|
| `botscope` not found | `pip install -e .` and confirm scripts on PATH |
| Import errors | Install from repo root; `pythonpath` should include `src` |
| GUI fails | `pip install 'botscope[gui]'` |
| Empty analysis | Confirm combined/common log format; try `botscope demo` |
| Doctor warns on network | Expected if contribution enabled; default is OFF |
| Need support zip | `botscope doctor --bundle support.zip` (sanitized) |

Still stuck? Open a bug report with sanitized doctor output.
