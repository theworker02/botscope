# FAQ

**Is network upload on by default?** No. Contribution is OFF by default.

**Can BotScope estimate global bot traffic?**  
It depends which surface you mean:

- **Local Observatory / a single log or PCAP:** reports **dataset-scoped** shares only. Do not treat one sensor as the whole Internet.
- **Global Observatory:** builds an **Internet-wide census** from federated zero-auth public sources (crawler IP panels, crawl catalogs, and similar). Optional Cloudflare Radar CDN estimates require an explicit token and stay off until configured.
- **Gated Internet headline:** may open only when reliability rules are met (for example ≥2 weighted traffic shares with uncertainty). Otherwise BotScope keeps an honest **UNKNOWN** / insufficient-evidence posture rather than inventing a global percentage.

See `docs/research/GLOBAL_ESTIMATION.md` and the Global Observatory UI.

**What does DEMO mean?** Synthetic/example data. Never publish demo outputs as observational results. The GUI shows a DEMO DATA banner on the bundled corpus.

**Why so many UNKNOWN labels?** Preferring UNKNOWN over forced certainty is a design goal.

**Is confidence a probability?** No — it is a heuristic score.

**Do I need an account or API key?**  
No for local log/PCAP analysis and the bundled demo. Global federation uses public sources without an account; Radar is optional.

**How do I try BotScope in under a minute?**

```bash
pip install botscope
botscope hello
# GUI:
pip install 'botscope[gui]'
botscope
```

**Where does data live?** Locally (sessions, preferences). Network contribution defaults OFF.

**Acquisition / commercial?** See [`ACQUISITION.md`](../../ACQUISITION.md) and [`COMMERCIAL.md`](../../COMMERCIAL.md).
