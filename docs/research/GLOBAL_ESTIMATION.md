# Global Estimation Methodology

**Status:** IMPLEMENTED (gated headline)

## Principle

BotScope federates heterogeneous observations without pretending they form a census of the Internet. When methodology criteria pass, it exposes an **INTERNET BOT TRAFFIC ESTIMATE** built from weighted traffic-share panels — never an equal-weight mean of unrelated sources.

## Release gate

Default / incomplete panel:

**MULTI-SOURCE BOT TRAFFIC OBSERVATIONS**

When criteria pass:

**INTERNET BOT TRAFFIC ESTIMATE**

Criteria (all required):

1. Multiple meaningful *traffic-share* observations exist (≥2 independent `source_id`s)
2. Source populations are documented
3. A defensible weighting model is applied (`population_reliability_v1` — equal-weight averaging is prohibited)
4. Temporal alignment is considered (ALIGNED / PARTIAL / MISALIGNED)
5. Source dependence / overlap is stated (UNKNOWN unless documented)
6. Uncertainty is computed (weighted dispersion + finite-sample floor → 95% interval)
7. Validation tests pass (`tests/estimation/`)

## Weighting model (`population_reliability_v1`)

Priority order per observation:

1. Explicit `extras.weight`
2. `extras.coverage_mass`
3. `log10(event_count + 10)` for local sensors
4. Documented reliability priors (e.g. Cloudflare Radar 0.50, local sensor 0.35, other 0.20)

Weights are normalized to sum to 1.0. Common Crawl catalog metrics are **not** traffic shares and never enter the headline.

## Source populations (examples)

| Source | Population |
|--------|------------|
| Common Crawl collinfo | Crawl index catalog — **not** HTTP traffic share |
| Cloudflare Radar | Cloudflare-observed HTTP requests |
| Local sensor | Authorized local logs/captures |

## Prohibited

```text
internet_bot_rate = mean(source_rates)
```

unless a published methodology specifically justifies equal weights (BotScope does not).

## Current algorithm

`estimate_from_federation` / `internet_wide_estimate` (`botscope.estimation.internet`):

- Collects normalized observations
- Filters to traffic-share metrics only
- Applies `population_reliability_v1`
- Builds coverage scorecard + explainer for the GUI
- Opens `INTERNET BOT TRAFFIC ESTIMATE` when gate criteria pass

## Uncertainty

Intervals appear when the multi-source panel qualifies — weighted dispersion with a finite-sample floor, clipped to `[0, 1]`. No fake precision beyond that.
