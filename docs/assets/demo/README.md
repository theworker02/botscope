# Demo media

Interim assets for the README **Video demo** section live here until a narrated screen recording is published.

| File | Status |
|------|--------|
| `botscope-tour.gif` | **Present** — animated page tour from real GUI screenshots (demo data) |
| `botscope-tour-strip.png` | **Present** — static strip of Observatory / Global / Events / Bot Library |
| `botscope-demo.mp4` | **Optional** — produced by `scripts/build_demo_gif.py` when `ffmpeg` is on PATH; otherwise leave as placeholder |
| `botscope-demo.webm` | **Placeholder** — alternate container if preferred |

## Recording script (≈45–90 seconds)

Use the bundled demo so the **DEMO DATA** banner is visible. Do not type or paste API tokens.

1. **Launch** — From a clean terminal: `botscope gui` (or `botscope`). Skip or dismiss Welcome.
2. **Load demo** — Click **Demo** on the toolbar. Wait until the status bar shows `[DEMO DATA]` and the yellow demo banner appears on Observatory.
3. **Observatory KPIs** — Pause on Automated / Human-likely / Unknown cards; briefly show the composition ring and Traffic Pulse (no need to invent commentary about Internet-wide rates).
4. **Global** — Open the **Global** page. Show the zero-auth source graph and status chips. Optionally click **About optional Radar…** only to note it is optional — do not enter a token on camera.
5. **Events** — Open **Events**. Optionally run a simple filter (e.g. category or the query bar). Select one row so the Classification Inspector populates.
6. **Close** — End on Observatory or Events with DEMO DATA still visible.

### Suggested ffmpeg capture (Windows, if installed)

```bash
# Adjust gdigrab title / region to the Observatory window as needed.
ffmpeg -f gdigrab -framerate 15 -i title="BotScope Observatory" -t 75 -c:v libx264 -pix_fmt yuv420p docs/assets/demo/botscope-demo.mp4
```

### After recording

1. Save as `docs/assets/demo/botscope-demo.mp4` (or `.webm`).
2. Update the root `README.md` **Video demo** section to link the MP4/WebM preferentially, keeping the GIF as a fallback for GitHub inline preview.
3. Confirm no token characters, production hostnames, or PII appear in any frame.

## Regenerating the GIF

```bash
python scripts/capture_docs_screenshots.py
python scripts/build_demo_gif.py
```
