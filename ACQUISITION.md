# Acquisition Brief â€” BotScope

**Date:** 2026-09-22  
**Repository:** https://github.com/theworker02/botscope  
**Default branch:** `main`  
**Primary language:** Python  
**Status:** Diligence briefing only. **No acquisition has occurred** by virtue of this file.  
**License:** Proprietary â€” sale, written commercial license, or completed asset transfer required (see root `LICENSE`).  
**Valuation:** Not stated.  
**Contact:** GitHub [@theworker02](https://github.com/theworker02) Â· [thanks.dev/u/gh/theworker02](https://thanks.dev/u/gh/theworker02)

> Cloning or forking this repository does **not** grant production, redistribution, SaaS, OEM, or commercial rights.

---

## 1. Executive thesis

This project is **proprietary**. Production use, redistribution, and commercial deployment require a written commercial license or completed acquisition. See [LICENSE](./LICENSE) and [ACQUISITION.md](./ACQUISITION.md). Contact [@theworker02](https://github.com/theworker02). <img src="docs/assets/botscope-logo.svg" alt="BotScope" width="480"/> **Python-first observability for an Internet-wide census of automated traffic.**

**Why a buyer cares:** BotScope packages transferable product IP â€” source, docs, in-repo brand assets, and a diligence room under `docs/acquisition/` â€” under a clear proprietary posture so diligence can proceed without mistaking the repo for open source.

---

## 2. Product snapshot

| Item | Detail |
|------|--------|
| Product | BotScope |
| Repo | `theworker02/botscope` |
| Language | Python |
| Open source? | **No** â€” proprietary |
| Rightsholder | theworker02 |
| Diligence pack | `docs/acquisition/` |

### Capability highlights (from current materials)

- Build a **worldwide automation census** in Global Observatory from federated zero-auth public sources (crawler IP ranges, Common Crawl catalog, and similar) plus optional Cloudflare Radar CDN estimates
- Classify requests from combined/common access logs (and optional PCAP / live paths)
- Separate **OBSERVED** totals from **CLASSIFIED** shares, with provenance badges
- Keep an honest **UNKNOWN** outcome instead of forcing certainty
- Explore both **global census views** and local sessions in a **native desktop Observatory** (Qt / PySide6 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â not a website)
- **Not** limited to a single site or sensor ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Global Observatory is the Internet-wide census surface
- **Not** a claim that one local log alone equals the whole Internet (local shares stay labeled local; the census comes from federated global sources)
- **Not** a cloud SaaS ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â analysis and preferences stay on your machine by default
- **Not** a substitute for authorization: only analyze systems and traffic you own or have permission to measure
- **Internet-wide census**: Global Observatory is the census product ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â federated public panels and optional CDN estimates.
- **Local-first**: sessions and preferences stay on disk unless you explicitly enable network contribution.
- **Provenance-aware**: OBSERVED counts are never relabeled as CLASSIFIED shares; local KPIs stay distinct from the global census.

---

## 3. Problem / opportunity

Teams evaluating BotScope typically need either (a) a commercial right to run or embed it, or (b) outright ownership of the Product IP for strategic build-out. Public GitHub visibility without a proprietary license creates false assumptions about free production use. This brief and the linked data room make the commercial path explicit.

---

## 4. What ships today

Honest maturity: treat repository contents, README claims, tests, and release tags as the source of truth. Do not assume production customers, ARR, filed patents, or SLAs unless separately evidenced in diligence.

Typical transferable surfaces:

- Source tree and build/test scripts present in-repo
- Documentation and design notes
- Acquisition / diligence markdown under `docs/acquisition/`
- Branding assets committed to the repository (if any)

---

## 5. Demo / evaluation path (buyer)

Minimal path (no secrets required unless README says otherwise):

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

Extended evaluation: `docs/acquisition/BUYER_EVALUATION.md`. Written NDA / evaluation grants may be required for private materials.

---

## 6. What a transaction typically includes

Subject to definitive schedules:

| Included (typical) | Excluded (typical) |
|--------------------|--------------------|
| Repo materials + asserted original IP | Seller personal accounts / unrelated repos |
| Docs + diligence room at closing | Third-party dependency source under separate licenses |
| In-repo brand marks as assigned | Secrets without rotation plan |
| Know-how captured in docs | Fabricated revenue, user, or adoption metrics |

---

## 7. Suggested deal structures

| Structure | When it fits |
|-----------|--------------|
| Non-exclusive commercial license | Deploy/run under seat or environment terms |
| Exclusive field-of-use license | Buyer wants exclusivity; seller may retain entity |
| Asset / IP assignment | Buyer wants ownership of Materials outright |
| OEM / redistribution | Separate agreement â€” not implied here |

Commercial terms (price, earnouts, escrow) are negotiated under NDA with counsel.

---

## 8. Buyer diligence checklist

- [ ] Confirm Rightsholder identity and authority to sell/license
- [ ] Inventory Materials (`docs/acquisition/ASSET_INVENTORY.md`)
- [ ] Review IP posture (`IP_PROVENANCE.md`) and dependencies (`DEPENDENCY_INVENTORY.md`)
- [ ] Run evaluation script (`BUYER_EVALUATION.md`)
- [ ] Review risks (`RISK_REGISTER.md`)
- [ ] Agree transfer scope (`TRANSFER_MANIFEST.md`) and handoff (`HANDOFF_CHECKLIST.md`)
- [ ] Supersede root `LICENSE` at closing via definitive agreement

---

## 9. Related documents

| Document | Purpose |
|----------|---------|
| `LICENSE` | Proprietary â€” no default grant |
| `docs/acquisition/README.md` | Data-room index |
| `docs/acquisition/EXECUTIVE_SUMMARY.md` | One-page thesis |
| `README.md` | Product overview |
| `SECURITY.md` | Vulnerability reporting |
| `COMMERCIAL.md` | Licensing contact path |
| `.github/FUNDING.yml` | Sponsors / thanks.dev |

---

## 10. Disclaimer

This package is informational and **does not** create a binding offer, grant of rights, or investment advice. Engage counsel for any transaction.

---

*Document version: 2.0.0 / 2026-09-22 Â· Classification: acquisition briefing*
