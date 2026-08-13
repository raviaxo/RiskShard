# 🔷 RiskShard

**A governed commons of public cyber-loss evidence, labelled well enough to tell you
when not to use it.**

### ▶ [Read the evidence live in your browser](https://raviaxo.github.io/RiskShard/) — no install

Open any number and read the exact public source it came from, what quantity it
actually measures, whose population it was measured on, what it cannot support — and
dispute it in one click. Prefer the terminal? [Jump to the one-command demo](#try-it-in-one-command).

## What RiskShard is — and isn't

**It is** a governed evidence object: a public figure carrying the label a
practitioner needs to decide whether it belongs in *their* model — what was observed,
who it was observed on, when, how it was measured, what statistical role it really
has, and what it can't end up supporting ([ADR-0010](docs/adr/0010-where-riskshard-stops.md)).

**It isn't** portable, and that is not a caveat — it is the finding. An org's controls,
threat environment, dependencies and time horizon are part of the thing being estimated,
so nothing travels intact. What we can do is label an observation well enough that you
can judge whether it travels to you. Fit is exposed as separate **facets** — geography,
sector, size, measurement basis — never a single score, because only you know which
mismatch matters for your scenario ([ADR-0011](docs/adr/0011-fit-is-a-facet-set.md)).

**The simulation is a reference rendering, not the product.** RiskShard stops at
governed evidence with its limits declared; quantification is your step. The engine is
kept because it is the mechanism that finds our own defects — every finding below exists
because something composes these anchors into a distribution and the result could be
inspected. It is never offered as the thing being sold.

**And it isn't finished.** A shard that clears the automated gate is a *review
candidate*, never "benchmark-grade" — that stays a recorded human decision.

## What we found in our own numbers

The point of governing evidence is that it lets you measure your own defects. These are
ours, each derived mechanically and re-runnable, and each published before anyone asked:

- **None of the 11 `impact.likely` anchors is a calibrated mode**, though the sampler
  treats it as one — and no value in the 18-entry measurement vocabulary denotes a mode,
  so the schema could not express one. **8** carry a published mean or median instead;
  **7** use a central tendency as a floor, which is not a lower bound on loss.
- **4 of 22 parameter families are coherent.** The other 18 compose anchors that measure
  different quantities, each validly sourced, none a reading of the same thing.
- **7 of 11 impact maxima carry no exceedance probability.** They say a loss this size
  happened, not how often a loss is worse.
- **Two published claims retracted** after measurement contradicted them, including one
  asserted in writing to a dataset maintainer before it was checked.

None of this says the sources are wrong, and none of it says the outputs are too high or
too low — a shard describes a *cell*, not a company, so "too high" has no referent.

## The question RiskShard answers

> Given my geography, industry, company size, and threat concern: what public evidence
> exists, what does each figure actually measure, how far is it from my context, and
> what can it not be made to support?

**One decision, made out loud:**
[How much ransomware cover should an Australian mid-market financial firm buy?](docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md)
— the model, the seed, the exceedance table, the recommendation, and the reason the
obvious answer is wrong. It is also where the governance layer stops being bookkeeping:
the shard's `impact.max` is one company's disclosed loss with no exceedance probability
attached, and swapping it alone moves the chance a single event exceeds AUD 20M from
0% to 23%. The limit decision is a decision about that one anchor.

## Try it in one command

```bash
git clone https://github.com/raviaxo/RiskShard.git && cd RiskShard
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt   # Python 3.9+
python scripts/riskshard_console.py
riskshard> demo
```

`demo` runs the whole first-run path automatically on a real shard: select ->
inspect the trust boundary -> simulate -> explain -> export a report -> show the
next gap. Every step is a real command you can also type yourself.

Prefer a single non-interactive command? This runs the same demo end to end and
prints the sourced numbers, confidence, and honest caveats — nothing to type,
so you can verify the "every number is traceable" claim in one shot:

```bash
printf 'demo\nexit\n' | python scripts/riskshard_console.py
```

## Honest status

RiskShard is a working practitioner beta, not a finished product. Shards are
labeled by maturity: `governed_starter`, automated `benchmark_candidate`, and —
only after a recorded human review decision — benchmark-grade. "Automated
benchmark-ready" is never the same as "human-approved benchmark-grade," and the
distinction stays visible everywhere results appear.

## Progress over time

Data strength is tracked, not asserted. Each data-pack release records a snapshot
to the [progress ledger](docs/internal/strength_ledger.json); the table below is
regenerated with `python scripts/strength_ledger.py markdown` and shows how many
model parameters trace to a reviewed public source over time.

<!-- strength-ledger:begin (regenerate with: python scripts/strength_ledger.py markdown) -->
| Release | Date | Source-backed params | Cell-matched | Shards 6/6 | Bridged/est. |
| --- | --- | --- | --- | --- | --- |
| 2026.08.08 | 2026-08-08 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.07 | 2026-08-07 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.03 | 2026-08-03 | 66 / 66 | 31 | 11 / 11 | 0 |
| 2026.08.02 | 2026-08-02 | 66 / 66 | 31 (+3) | 11 / 11 | 0 |
| 2026.08.01 | 2026-08-01 | 66 / 66 | 28 | 11 / 11 | 0 |
| 2026.07.24 | 2026-07-24 | 66 / 66 (+2) | — | 11 / 11 (+1) | 0 (-2) |
| 2026.07.24 | 2026-07-24 | 64 / 66 | — | 10 / 11 | 2 |
<!-- strength-ledger:end -->

A parameter moves from *bridged/estimated* to *source-backed* only through a
recorded evidence decision — so a rising source-backed count is real strengthening,
not relabeling.

## See the proof

Three artifacts show what "evidence-governed" buys you in practice.

**0. Challenge any number.** Every parameter answers the only question that matters —
*where did this come from?* — before you're asked. `challenge <parameter>` in the console
(or `python scripts/riskshard_modules.py provenance <shard> <parameter>`) shows the value,
the named source, the exact cited line, and the caveat in one look:

```text
frequency.max = 0.69 annual_probability   [source_backed · confidence medium]
  Source : Cyber Security Breaches Survey 2025/2026 (official_statistics, 2026-04-30)
  Quote  : ...large businesses experienced cyber breaches or attacks at 69%.
  Caveat : ...larger-organization prevalence may overstate mid-market frequency.
```

Disagree? `provenance <shard> --dispute <parameter>` prints a pre-filled GitHub issue URL
so a skeptic becomes a contributor in one click. A number you can trace is a number you
can dispute — that's the point.

**Citable.** Every parameter has a stable identifier, and the pinned form names an
immutable, fingerprinted release:

```text
RS:us_finance_bec_midmarket/impact.likely@2026.07.21-v0.1.0-stable
```

"Cite this number" on the [explorer](https://raviaxo.github.io/RiskShard/) copies a
citation with the value, the source, **the caveat**, and a permanent link — so a figure
quoted in a board deck or an audit workpaper carries its limitation with it, and still
resolves to what it said when it was written. Identifiers are never reused or deleted; a
renamed shard keeps resolving through `aliases.yaml`. Worked examples — a risk-register
row, a board-deck footnote, a prose sentence — are in [docs/CITING.md](docs/CITING.md);
the design is [ADR-0004](docs/adr/0004-citable-parameter-identifiers.md).

The whole system at once: [docs/EVIDENCE_REPORT.md](docs/EVIDENCE_REPORT.md) is every
parameter in every shard — value, source, and caveat — regenerated with
`python scripts/riskshard_modules.py provenance --all --report docs/EVIDENCE_REPORT.md`.

**1. A board-ready executive summary from a real run.** After `run`, the console
command `report exec` writes a one-page Markdown summary to `results/` — bottom-line
loss range, plain-language confidence, the sources behind it, and the honest caveats,
with no invented numbers. An excerpt from the UK finance data-breach shard:

```text
# Executive Risk Summary — United Kingdom Finance Data Breach Midmarket

## Bottom line
A data breach in this context is modeled to cost an average of GBP 3,530,067 per
year, with a 1-in-20 (P95) year reaching GBP 5,763,789 and a 1-in-100 (P99) year
reaching GBP 6,427,200. This is a modeled range built from public evidence, not a
prediction of a specific event.

## How much to trust it
Confidence: HIGH. 6 of 6 model parameters are backed by public sources.
  - Cyber Security Breaches Survey 2025/2026 (trust: high)
  - IBM UK Cost of a Data Breach 2025 release (trust: medium)
  - FCA fines Equifax Ltd over cyber security breach (trust: high)

## Key caveats (read before deciding)
- This is a benchmark candidate shard, not a human-approved benchmark.
- The FCA penalty stress anchor is a regulatory cap, not total event loss.
```

Reproduce it with `use gb_finance_data_breach_midmarket` → `run` → `report exec`.

**2. A worked contribution, source to preflight.** [docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md)
walks one real, accepted change end to end: it takes a single primary source (the IBM
Canada 2025 breach-cost release) through `sources → extractions → evidence →
calibrations → evidence pack → preflight`, upgrading the Canada shard's `impact.likely`
from a global bridge converted via FX to a Canada-specific **CA$6.98M** anchor — with
the limitations made *louder*, not quieter. Copy its shape to strengthen any shard.

## Product thesis

RiskShard aims to become a shared computation layer for cyber risk:

- Scenarios are YAML "risk shards" that can be reviewed, versioned, reused, and generated.
- Frequency and impact are modeled as distributions instead of fixed scores.
- Outputs focus on decision metrics such as expected loss, P95, and P99.
- The long-term direction is a library of defensible, benchmarked risk parameters that can be consumed by humans, applications, and AI agents.

## What Works Today

- Monte Carlo simulation using PERT or triangular distributions
- YAML scenario inputs with JSON Schema validation
- Portfolio aggregation across multiple scenarios
- Mean, P50, P95, and P99 loss metrics
- Loss Exceedance Curve chart generation
- Optional JSON report export
- Per-scenario RNG isolation and seed metadata for seeded JSON exports
- Interactive practitioner console for search, calibration, simulation, reports, and validation
- Local `doctor` command for environment, source, evidence, extraction, scenario, readiness, package, data-pack, and test-readiness checks
- Risk module catalog with `modules`, `info`, `use`, `packs`, `propose`, `calibrate`, and `run` workflows
- Evidence-pack registry that shows source gather dates, evidence ingestion dates, trust tier, confidence, renewal status, and remaining assumptions per module
- Country expansion priority map covering 25 countries so regional contributors can pick high-value evidence packs
- Reviewed source-to-extraction-to-evidence-to-calibration workflow
- Governed starter vs demo fixture labels in scenario metadata, CLI output, readiness, and console search
- Vetted YAML taxonomies and evidence matching for industry, country, company size, and threat context
- Conditional loss-chain modeling ([ADR-0001](docs/adr/0001-loss-chain-scenario-modeling.md)): a scenario can compose up to three downstream conditional loss stages, each gated by its own source-backed conditional probability, so an initiating event can carry — for example — a rare regulatory-penalty tail that a single-threat scenario cannot express
- Runnable top-risk threats beyond the country shards — insider misuse, third-party outage, and AI-enabled (deepfake) fraud now calibrate and simulate (five clean; third-party outage with one honestly-labeled frequency estimate), each governed-starter with source-backed frequency and loudly-caveated impact bridges

## In Progress

The decision engine is partially sketched but not fully integrated. The repository includes early control objects for frequency and impact reduction, a comparator, and orchestration notes. These pieces need cleanup before they should be treated as production-ready.

Emergent risk scenarios (AI-as-liability, correlated/systemic loss, governance/regulatory loss) are being built out per [docs/ROADMAP.md](docs/ROADMAP.md), starting governed-starter and maturing as evidence deepens.

## Repository Layout

```text
engine/                  Reusable simulation and control modules
engine/analysis/         Comparison helpers for before/after simulations
engine/controls/         Early control simulation layer
control_profiles/        YAML control transformation profiles
org_profiles/            YAML organization context profiles
provenance/              YAML source and evidence metadata
taxonomies/              Vetted IDs and labels for dropdown-style inputs
evidence/                Structured evidence records for benchmark matching
extractions/             Reviewed source fact extractions mapped to evidence
calibrations/            Calibration profiles and FX assumptions
threat_library/          Starter threat scaffold for future top-risk workflows
risk_modules/            Practitioner-facing module descriptors
sources/                 Curated source registry and generated gather manifest
library/benchmarks/      Legacy benchmark fixture data
scenarios/               YAML risk shards and demo fixtures
schemas/                 JSON Schema for scenario validation
scripts/                 Thin CLI and console entry points
tests/                   Stdlib unittest coverage
results/                 Ignored local reports and LEC charts
docs/                    Methodology, architecture, and contributor guides
```

## Run The Full Portfolio

Beyond the guided `demo` above, you can run every scenario at once:

```bash
python scripts/fair_calc.py scenarios --trials 10000 --dist pert --seed 42 --export
```

The command above runs every YAML scenario in `scenarios/`, prints portfolio statistics, saves a Loss Exceedance Curve to `results/`, and writes a JSON report when `--export` is included. The scenario folder mixes calibrated-workflow starters with older demo fixtures; see [scenarios/README.md](scenarios/README.md) before treating portfolio output as decision-ready.

When a folder mixes scenario currencies or has fixtures without currency
metadata, the CLI prints a mixed-currency warning. Portfolio totals are then an
unconverted arithmetic sum, useful for smoke testing but not for financial
decision-making.

## Interactive Console

For a guided practitioner workflow, start the console:

```bash
python scripts/riskshard_console.py
```

Or start the local browser console:

```bash
python scripts/riskshard_web_console.py
```

Then try:

```text
riskshard> workflow
riskshard> toprisks
riskshard> modules
riskshard> countries
riskshard> countries GB
riskshard> modules info gb_finance_data_breach_midmarket
riskshard> packs gb_finance_data_breach_midmarket
riskshard> doctor
riskshard> readiness
riskshard> next
riskshard> feeds
riskshard> use gb_finance_data_breach_midmarket
riskshard(gb_finance_data_breach_midmarket)> show options
riskshard(gb_finance_data_breach_midmarket)> show gaps
riskshard(gb_finance_data_breach_midmarket)> propose
riskshard(gb_finance_data_breach_midmarket)> calibrate
riskshard(gb_finance_data_breach_midmarket)> show evidence
riskshard(gb_finance_data_breach_midmarket)> explain
riskshard(gb_finance_data_breach_midmarket)> run
riskshard(gb_finance_data_breach_midmarket)> report json
riskshard(gb_finance_data_breach_midmarket)> report exec
```

`report exec` writes a one-page, board-ready Markdown summary to `results/` with
the modeled loss range in plain language, a confidence rating, the source-backed
trust boundary, honest caveats, and the accept/mitigate/gather-evidence/localize
decision options. It is decision support, not assurance.

The console keeps all artifacts local and reviewable in `results/`. See [docs/CONSOLE_EXPERIENCE.md](docs/CONSOLE_EXPERIENCE.md).

The browser console groups the workflow into four lanes: run a shard, improve
evidence, govern data, and contribute country. After a module is selected, the
dashboard shows contextual actions and a six-parameter coverage matrix so users
can see which values are source-backed versus assumption-only. Coverage cells
and module rows are actionable: source-backed cells open the evidence pack, and
assumption or missing cells open the calibration proposal for that module.

## Evidence and calibration

Generate a draft calibrated scenario from reviewed evidence:

```bash
python scripts/calibrate_scenario.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --evidence evidence \
  --calibration calibrations/au_finance_ransomware.yaml \
  --threat ransomware \
  --report-output results/au_finance_ransomware_calibration.json \
  --scenario-output results/au_finance_ransomware_calibrated.yaml
```

The report shows the bottom line, confidence, what changed, selected vs. excluded
evidence, normalization and FX assumptions, and the generated ranges. FX
assumptions live in `calibrations/fx_rates.yaml` (each rate sourced and dated; see
[docs/FX_RATE_REFRESH.md](docs/FX_RATE_REFRESH.md)).

Other governance and inspection commands (each also reachable from the console):

```bash
python scripts/validate_evidence.py            # evidence quality gates
python scripts/data_governance.py              # source freshness / trust / renewal
python scripts/readiness_dashboard.py          # coverage, gate, next actions
python scripts/riskshard_doctor.py             # local environment + data health
python scripts/riskshard_modules.py list       # risk modules and evidence packs
python scripts/riskshard_modules.py coverage   # data-strength grade per shard
python scripts/contributor_preflight.py path/to/proposed_pack  # before a PR
```

See [docs/CONSOLE_EXPERIENCE.md](docs/CONSOLE_EXPERIENCE.md) for the guided
workflow and [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution path.
## Installable Commands

RiskShard can still be run directly from `scripts/`, but `pyproject.toml` also declares console entry points for packaging:

- `riskshard`
- `riskshard-calibrate`
- `riskshard-console`
- `riskshard-web-console`
- `riskshard-feeds`
- `riskshard-readiness`
- `riskshard-data-pack`
- `riskshard-preflight`
- `riskshard-doctor`
- `riskshard-modules`
- `riskshard-toprisks`
- `riskshard-weekly`
- `riskshard-package-smoke`
- `riskshard-benchmark`
- `riskshard-beta`

## Tests

```bash
python -m unittest discover -s tests
```

The tests cover schema validation, simulation behavior, portfolio aggregation, control transformations, and a CLI smoke test against the sample scenarios.

## Generated Outputs

Routine CLI outputs are written to `results/` and ignored by Git. If an output becomes a curated example, move it to a documented examples location before committing it.

## Scenario Format

Each scenario currently contains metadata plus annualized frequency and single-event impact ranges:

```yaml
metadata:
  name: Ransomware Attack
  version: "1.0"

frequency:
  min: 0.1
  likely: 0.3
  max: 0.7

impact:
  min: 50000
  likely: 150000
  max: 500000
```

The schema is intentionally small at this stage. The strategic question is whether RiskShard should remain a minimal simulation schema or evolve into a richer FAIR-style ontology for threat events, loss forms, controls, assumptions, confidence, and data provenance.

## Input Files

Organization profiles live in `org_profiles/` and include:

- `org_type`
- `industry`
- `country`
- `employees`
- `annual_revenue_or_budget`
- `data_sensitivity`
- `internet_exposure`
- `third_party_dependency`
- `regulatory_intensity`

Organization profiles are used for evidence matching to find the most relevant evidence records for a specific organization context.

RiskShard does not currently apply heuristic contextual multipliers. To model a specific organization, generate an explicit calibrated scenario from reviewed evidence and simulate that scenario with the standard CLI. See [docs/org_specific_scenarios.md](docs/org_specific_scenarios.md).

Control profiles live in `control_profiles/` and remain transformations over the scenario, not embedded scenario properties.

Provenance files live in `provenance/` and label every evidence record as `source_backed`, `estimated`, or `synthetic`. The canonical Australia finance ransomware example now uses public source-backed evidence for all six direct frequency and impact parameters, plus sector applicability and regulatory context. It is ready for human benchmark review, but still carries caveats around reused sector frequency and global tail-loss bridge evidence.

Taxonomies live in `taxonomies/` and are the vetted source for dropdown-style IDs such as `financial_services`, `AU`, `mid_market`, and `ransomware`.

Evidence records live in `evidence/`. They are separate from scenarios: evidence records capture extracted facts and applicability, while scenarios remain simulation-ready inputs. Evidence matching explains whether each record is an exact match or a fallback for the supplied organization profile and threat.

Risk modules live in `risk_modules/`. They do not change the simulation schema;
they describe the practitioner workflow around a shard: scenario, default
organization profile, calibration profile, evidence pack, reviewed extractions,
controls, tags, and what the module is or is not good for.

Source-backed evidence records should include `source_id` values that map to `sources/manifest.json`, plus a concise `citation_detail` describing where the fact appears in the source. Estimated or synthetic model assumptions must remain labeled as `estimated` or `synthetic`.

Reviewed extraction records live in `extractions/` and document the fact pulled from a source before it becomes one or more structured evidence records.

The starter threat library lives in `threat_library/`. The summary below is exactly
that — a summary. The **live, authoritative coverage** comes from the tools, which
own this fact and never drift:

```bash
python scripts/riskshard_modules.py coverage   # data-strength grade per country shard
python scripts/riskshard_toprisks.py           # top-risk calibration status
```

**Country shards — 11 modules across 8 countries (AU, CA, DE, FR, GB, JP, SG, US).**
All eleven are 6/6 source-backed across business email compromise, data breach, and
ransomware — every BEC shard (US, AU, SG) is fully source-backed, and
`gb_finance_data_breach_midmarket` is the only shard whose evidence is entirely
cell-matched. Source-backed does not mean cell-matched: the per-parameter population
status (cell-matched vs bridged, and on which dimension) is on the
[explorer](https://raviaxo.github.io/RiskShard/) and in the evidence report — that split
is the honest headline, and the coverage tools above are the authoritative view.

**And cell-matched does not mean coherent.** A second, independent axis
([ADR-0007](docs/adr/0007-construct-coherence.md), added 2026-08-07 after a practitioner
asked the question in the open): every record now declares *what quantity* it measures,
and a range is `mixed` when its `min`/`likely`/`max` do not share one basis. Portfolio-wide
that is **4 coherent · 18 mixed of 22 parameter families — every shard carries at least one
mixed range, and no impact range is coherent.** `gb_finance_data_breach_midmarket` is the
sharpest example precisely *because* it is fully cell-matched: its impact range runs a
self-reported *perceived* cost, an *average total* breach cost, and an FCA *regulatory
penalty* — three different quantities, each correctly sourced. Mixed is declared, not
hidden, and which mixes are acceptable is an open question in the ADR rather than a settled
call. Read the two axes together; neither alone tells you a range is safe to use.

**And a maximum here is not a bound.** Measuring the second axis exposed a third
([ADR-0008](docs/adr/0008-the-governed-tail.md), accepted 2026-08-07): every `impact.max` now
declares *what is known about it being exceeded*. Portfolio-wide, **2 of 11 maxima carry an
exceedance statement — 0 are modeled quantiles, 2 are observed ranks (1 of 579 claims, 1 of
84), 2 are legal ceilings, and 7 carry nothing at all.** That is not a footnote: in
[the worked decision](docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) the per-event mean runs
**14.8× its own mode** because the maximum drives the distribution rather than bounding it,
and moving that one anchor swings P(event > AUD 20M) from **0% to 23%** — so the least
evidenced anchor is the one the answer is most sensitive to. Unless a row says otherwise,
treat every `impact.max` here as *the largest loss we found*, never *the largest loss that
can happen*. Where an exceedance rate **is** stated it is a within-sample rate on insured
claims, and therefore a floor: losses above it are more common than the sample says, not
less. Run `python scripts/riskshard_modules.py exceedance` to see all eleven.

**And that maximum is doing most of the work.** The model composes min/likely/max into one
distribution whose mean is a weighted blend of the three, so each anchor's contribution is
exactly computable. **7 of 11 shards take most of their modeled per-event loss from
`impact.max` alone — and 4 of those maxima declare `none_known`.** Leverage runs from 33%
to **95%**: on `au_finance_ransomware_midmarket`, 95% of the modeled per-event loss comes
from one documented event carrying no exceedance probability, and doubling that single
anchor moves the published annual average by +94%. That is the number to interrogate first
in any shard here. `python scripts/riskshard_modules.py tail` prints the whole table.

**Top-risk threats — all six now runnable, not merely evidenced.** Business email
compromise, data breach, ransomware, insider misuse, and AI-enabled (deepfake) fraud
calibrate and simulate cleanly; third-party outage calibrates with one honestly-labeled
frequency estimate. Insider misuse and third-party outage rest on source-backed frequency
bridges plus **generic cross-cyber impact bridges** (loudly caveated as *not*
insider/outage-specific) — governed-starter, not benchmark-grade.

Every shard stays on the maturity ladder: **6/6 source-backed is data strength, not a
human-approved benchmark.** A grade never implies benchmark-grade — that remains a
recorded human decision in the ledger.

## Source Baseline

RiskShard can gather a curated baseline of public source materials and write an auditable manifest:

```bash
python scripts/gather_sources.py
```

The source registry lives in `sources/registry.yaml`. The generated manifest lives in `sources/manifest.json` and records each source's publication date, gather timestamp, final URL, HTTP status, content type, byte count, SHA-256 hash, and raw artifact path. Raw downloaded artifacts are stored under `sources/raw/` and ignored by Git.

Gathering a source does not automatically make it a benchmark parameter. Extracted facts should still be reviewed and stored as evidence records with applicability, confidence, limitations, and honest evidence-type labels.

## Documentation

Start with [docs/README.md](docs/README.md). Key docs:

- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — the model, its limits, and the accountability stance.
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute, including the DCO sign-off.
- [docs/architecture.md](docs/architecture.md) — engine, evidence, and calibration architecture.
- [docs/CONSOLE_EXPERIENCE.md](docs/CONSOLE_EXPERIENCE.md) — the interactive console workflow.
- [docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md) — a source taken end-to-end to a passing contribution.
- [docs/ROADMAP.md](docs/ROADMAP.md) — emergent risk scenarios (AI-as-liability, systemic, regulatory) and their sequencing.
- [docs/adr/](docs/adr/) — architecture decision records, including ADR-0001 (loss-chain scenario modeling).

## License

Copyright (C) 2026 Sergio Alonso.

RiskShard is free software, licensed under the **GNU Affero General Public License
v3.0 (AGPL-3.0)**. You may use, study, share, and modify it under those terms; if
you run a modified version as a network service, the AGPL requires you to offer
that service's users the corresponding source. See [LICENSE](LICENSE).

Contributions are accepted under the same license via the Developer Certificate of
Origin (DCO) — sign off your commits with `git commit -s`. See
[CONTRIBUTING.md](CONTRIBUTING.md).
