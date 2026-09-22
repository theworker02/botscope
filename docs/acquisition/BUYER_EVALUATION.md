# Buyer evaluation â€” BotScope

## Goal

In 15â€“45 minutes, verify the Product builds or runs as documented and that proprietary notices are present.

## Steps

1. Confirm root `LICENSE` is proprietary and `ACQUISITION.md` exists.
2. Skim `README.md` install/run claims.
3. Execute:

```
```bash
pip install botscope
botscope hello
```
```bash
botscope hello --keep-session hello.bscope
botscope hello --json
```
```bash
botscope access
pip install "botscope[gui]"   # if you want the Observatory
botscope gui
```
```bash
pip install "botscope[gui]"
```
```bash
pip install botscope
```
```bash
git clone https://github.com/theworker02/botscope.git
cd botscope
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[gui,dev]"
```
```bash
botscope doctor
botscope hello
botscope demo --output demo_analysis.bscope
botscope open demo_analysis.bscope
```
```bash
botscope gui
# or simply: botscope
```
```bash
botscope analyze path/to/access.log --output analysis.bscope
botscope report analysis.bscope --format markdown --output report.md
```

4. Run tests if present (`npm test`, `pytest`, `cargo test`, `go test ./...`, etc.).
5. Record README vs observed behavior gaps in workpapers.

## Pass criteria

- [ ] Clone succeeds
- [ ] Documented happy path works **or** failure is explained
- [ ] Minimal path needs no surprise secrets
- [ ] License notices intact

*Updated: 2026-09-22*
