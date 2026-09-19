# Documentation assets

Public media used by the root [README](../../README.md) and related docs.

Do **not** commit real API tokens, production logs with PII, or screenshots that show credential values.

## Inventory

| Path | Description |
|------|-------------|
| `botscope-logo.svg` | Wordmark + radar-scope mark (preferred for README header) |
| `botscope-icon.svg` | Square app icon mark |
| `botscope-mark.png` | Raster mark (generated companion to the SVG icon) |
| `screenshots/observatory-dashboard.png` | Observatory with DEMO DATA banner, KPIs, composition ring |
| `screenshots/global-observatory.png` | Global Observatory zero-auth source graph |
| `screenshots/events.png` | Events table + query bar |
| `screenshots/bot-library.png` | Bot Library known vs observed |
| `screenshots/sources.png` | Sources registry |
| `screenshots/settings.png` | Settings (Radar token field empty / placeholder only) |
| `demo/botscope-tour.gif` | Animated tour of main pages (interim demo) |
| `demo/botscope-tour-strip.png` | Static four-panel strip |
| `demo/README.md` | Recording script for a full MP4/WebM |

## Regenerating screenshots

From the repository root (GUI extras required):

```bash
pip install -e ".[gui]"
python scripts/capture_docs_screenshots.py
python scripts/build_demo_gif.py
```

The capture script loads the bundled demo corpus, clears any Cloudflare Radar token field before the Settings shot, and writes PNGs under `screenshots/`.

## Design notes

- Palette aligns with the Instrument theme (deep slate chrome + teal accents, Bahnschrift UI type), not purple “AI” gradients.
- Screenshots intentionally show the **DEMO DATA** banner where applicable so readers know figures are synthetic.
- Captions and docs must not invent Internet-wide prevalence statistics.
- Capture script forces an expanded sidebar and clears the optional Radar token field.