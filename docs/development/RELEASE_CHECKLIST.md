# Release checklist

Status: IMPLEMENTED (process)

- [ ] `pytest` green
- [ ] `ruff check src tests scripts`
- [ ] `python scripts/repo_audit.py` PASS
- [ ] `botscope doctor` overall ok/warn (not fail on core deps)
- [ ] DEMO outputs clearly labeled
- [ ] FEATURES.md / PROJECT_STATUS.md / CHANGELOG.md match reality
- [ ] No secrets in tree
- [ ] Network contribution still OFF by default
- [ ] CITATION.cff has no invented DOI
