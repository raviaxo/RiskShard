# RiskShard Methodology

This document is the canonical statement of the RiskShard model and its stance,
grounded in the engine code (`file:line` references throughout).

## What this document is

This is the honest description of the quantitative model behind a RiskShard
number: what it computes, why it is built this way, and — as importantly — what
it does **not** do. It is written so a practitioner or reviewer can judge whether
a shard's loss estimate is fit for their decision, and challenge it where it is
weak. Every mechanism below maps to code in `engine/fair_calc.py`; nothing here
is aspirational.

The controlling claim discipline: **"automated benchmark-ready" is not
"benchmark-grade."** A number that runs is not a number that has been reviewed.
A shard is only called benchmark-grade after a recorded human review decision.
RiskShard's durable asset is an *accountable* trust/provenance layer, not model
sophistication.

## The model in one paragraph

Each risk shard is a single loss-event model in the FAIR family. A scenario
declares two three-point estimates — an annualized **frequency** and a
per-event **impact** — each as `{min, likely, max}`. A Monte Carlo run draws one
frequency and one impact per trial from their distributions and multiplies them
into a per-trial annualized loss (`sampled_frequency * sampled_impact`,
`engine/fair_calc.py:100-102`). Ten thousand trials produce a loss
*distribution*, from which RiskShard reports the mean, median, and the p95/p99
tail, plus a Loss Exceedance Curve. That is the entire core; the rest of the
repository is the evidence-provenance spine that decides what the six input
numbers are allowed to be.

## The scenario format

The schema (`schemas/shard_schema.json`) is deliberately minimal:

```yaml
frequency: { min: ..., likely: ..., max: ... }   # events per year
impact:    { min: ..., likely: ..., max: ... }    # loss per event, in the shard's currency
metadata:  { name: ..., currency: ..., ... }
```

Two three-point ranges, six numbers. Organization context, controls,
provenance, and calibration are **separate inputs**, never embedded in the
scenario. This keeps the simulated object
small and auditable and keeps "what we believe" (the scenario) distinct from
"why we believe it" (the evidence pack).

## Why Monte Carlo rather than a point estimate

The classic three-point shortcut collapses a range to a single expected value —
e.g. PERT's `E = (min + 4·likely + max) / 6`. That number is worse than useless
for a risk decision, because **risk lives in the tail, and a mean hides the
tail.** Two shards can share a mean while one is bounded and the other is
fat-tailed; the mean cannot tell them apart, and the fat-tailed one is what puts
an organization out of business.

Monte Carlo keeps the whole shape. By sampling the frequency and impact
distributions thousands of times and forming the empirical loss distribution,
RiskShard can report:

- the **median** (`p50`) — the typical year,
- the **p95 / p99 tail** (`compute_stats`, `engine/fair_calc.py:115-123`) — the
  bad and very-bad years a board actually needs bounded,
- a **Loss Exceedance Curve** (`plot_lec`, `engine/fair_calc.py:221-244`) —
  "probability that annual loss exceeds X," the native language of risk appetite.

So the choice is not "Monte Carlo vs. PERT" as rival distributions — it is
"sample the distribution vs. collapse it to one number." RiskShard uses PERT (or
triangular) *as* the per-parameter shape and Monte Carlo to propagate it into a
loss distribution instead of a scalar.

## The distributions

`--dist` selects how each three-point range is turned into draws
(`sample_range`, `engine/fair_calc.py:79-84`):

**Modified-PERT (default).** A Beta distribution reparameterized from
`{min, likely, max}` (`beta_pert`, `engine/fair_calc.py:69-76`):

```
alpha = 1 + λ · (likely − min) / (max − min)
beta  = 1 + λ · (max − likely) / (max − min)
sample = min + Beta(alpha, beta) · (max − min)
```

with the shape weight **λ = 4 fixed in code** (the standard Vose modified-PERT
value). λ=4 concentrates mass around `likely` while keeping smooth, bounded
tails — a reasonable default for expert three-point estimates. It is **not**
currently exposed on the CLI; a shard cannot yet tune how sharply it trusts its
own mode. That is a known limitation, not a hidden feature (see Limits). If
`min == max` the sampler degenerates to the point value.

**Triangular (`--dist triangular`).** `rng.triangular(min, max, likely)` — a
lighter-weight alternative with linear density and harder shoulders. Useful as a
sensitivity check: if a shard's p95 swings materially between `pert` and
`triangular`, the result is being driven by distribution choice rather than by
evidence, which is itself a finding.

Neither distribution invents information beyond the three declared points. The
model is exactly as good as those points, which is why provenance — not the
sampler — is the real product.

## The frequency / severity asymmetry (the honest core)

**Frequency and severity are not equally knowable, and the current model treats
them as if they were.** This is the most important caveat in RiskShard.

- **Frequency** — "how often does a firm in this cell (country × industry × size
  × threat) suffer this event per year" — is comparatively tractable. It is a
  rate, it is estimable from prevalence surveys and denominator-aware breach
  statistics, and it is genuinely shared across firms in a cell.
- **Severity / impact** — "how much does one event cost *this* firm" — is only
  weakly predictable from the same cell index. Loss-per-event is heavy-tailed,
  strongly org-specific (data footprint, revenue, response maturity, regulatory
  exposure), and poorly captured by a single national or sector average.
  Cell-indexing carries far less information about severity than about
  frequency.

In today's engine both parameters use the identical three-point PERT machinery,
which **implies impact-by-cell is as trustworthy as frequency-by-cell. It is
not.** RiskShard should widen and more loudly caveat impact intervals relative to
frequency intervals rather than presenting symmetric confidence. Until it does,
read every shard's impact band as *more* uncertain than its width suggests, and
treat the p95/p99 loss tail as directional, not precise. This asymmetry is a
first-class limitation, deliberately surfaced here rather than buried.

## Portfolio aggregation and its assumptions

Across a folder of shards, the portfolio loss for each trial is the **arithmetic
sum of the per-shard losses at that trial index** (`aggregate_portfolio`,
`engine/fair_calc.py:107-112`), and statistics are computed on that summed
series. Two assumptions are baked in and must be stated:

1. **No dependency structure.** Shards are sampled with independent per-scenario
   RNG streams and summed. RiskShard models **no correlation** between shards —
   no common-cause shocks (a shared vendor, a wormable CVE, a single threat actor
   hitting several units). Real portfolios have positive tail dependence, so the
   summed p99 here is likely an **under**-estimate of true joint tail risk. Do
   not read the portfolio tail as a modeled systemic-risk number.
2. **No currency conversion.** A mixed- or unspecified-currency portfolio is
   summed unconverted, and the run emits an explicit warning and refuses to name
   a portfolio currency (`engine/fair_calc.py:196-211`). The sum is arithmetic,
   not economic; convert deliberately via `calibrations/fx_rates.yaml`, never
   silently.

## The accountability stance (why the number is auditable)

The model is intentionally simple; the discipline is in provenance and
reproducibility. Three mechanisms make a RiskShard number accountable rather
than merely plausible:

1. **Reproducibility by construction.** When a seed is supplied, each scenario
   gets a derived seed from `sha256(base_seed : scenario_path : config
   fingerprint)` (`derive_scenario_seed`, `engine/fair_calc.py:55-58`), giving
   per-scenario RNG isolation. The exported report carries the seed, the config
   **fingerprint** (`scenario_fingerprint`, sha256 of the canonicalized config),
   and the exact **reproduction command** (`engine/fair_calc.py:138-179,
   247-259`). Any reviewer can re-run the identical numbers and detect if an
   input silently changed.
2. **Every parameter traces to a reviewed public source.** The spine
   `sources/manifest.json → extractions/ → evidence/ → calibrations/ →
   scenarios/` means each of the six input numbers is either backed by a cited,
   dated, reviewed source or **honestly labeled** as an estimate, synthetic
   value, or cross-country/-sector "bridge." Bridges and assumptions are never
   dressed up as local claims.
3. **Claim discipline is enforced separately from the code.** The engine can
   only ever produce an *automated* candidate. Whether a shard may be called
   benchmark-grade is a recorded human review decision, with its
   bridge/stress-anchor caveats required to stay visible in output and release
   notes.

The stance in one line: **show provenance, keep score, and make it trivial for
someone else to prove us wrong.** The frequency backtest against open incident
data (`scripts/backtest_frequency.py`) is the next expression of this — checking a
shard's predicted frequency against reality before the model is promoted. The
result, held to the same honesty, is in [BACKTEST_VALIDATION.md](BACKTEST_VALIDATION.md).

## Limits (explicit)

- **Single-loss-event form, not a compound process.** A trial multiplies one
  continuous frequency by one severity draw; it does not draw *N* events and sum
  *N* independent severities. For sub-annual or multi-event years this
  understates severity dispersion. Evaluating a Poisson frequency / compound
  model is a known future improvement.
- **Frequency modeled as a continuous rate, not a count.** See above; PERT-vs-
  Poisson for frequency is an open question the backtest begins to probe.
- **Impact uncertainty understated by symmetric treatment** (the
  frequency/severity asymmetry; a known future improvement).
- **No inter-shard correlation** in portfolio aggregation (tail risk
  under-stated).
- **λ = 4 is fixed**, so per-shard confidence in the mode is not tunable.
- **FX rates are static assumptions** in `calibrations/fx_rates.yaml` and need
  periodic refresh.
- **The model is only as good as six numbers.** No sampler compensates for thin
  or bridged evidence; coverage is data-capped (the France work proved this).

## How to challenge a shard

1. Re-run it with its printed reproduction command; confirm the fingerprint.
2. Open its evidence pack (`python scripts/riskshard_modules.py packs <id>`) and
   check which of the six parameters are source-backed vs. bridged vs. estimated.
3. Flip `--dist pert` ↔ `--dist triangular`; if the tail moves a lot, the result
   is distribution-driven, not evidence-driven.
4. Read the ledger caveats for that shard before quoting its number to anyone.

## Change control

This document states methodology, which is a public claim. Material changes to
the model, the distributions, the asymmetry stance, or the accountability
mechanisms require human review; they are not amended by editing this file alone.
