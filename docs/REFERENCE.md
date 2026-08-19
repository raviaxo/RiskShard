# Reference

*Operational reference for RiskShard: what the engine does, how to run it, the file
formats, and the layout. Moved off the README on 2026-08-19, when the front door was
measured at 599 lines / 4,761 words — a manual bolted onto a pitch. The README now
answers "what is this and why should I care"; this page answers "how do I run it".*

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
- Conditional loss-chain modeling ([ADR-0001](adr/0001-loss-chain-scenario-modeling.md)): a scenario can compose up to three downstream conditional loss stages, each gated by its own source-backed conditional probability, so an initiating event can carry — for example — a rare regulatory-penalty tail that a single-threat scenario cannot express
- Runnable top-risk threats beyond the country shards — insider misuse, third-party outage, and AI-enabled (deepfake) fraud now calibrate and simulate (five clean; third-party outage with one honestly-labeled frequency estimate), each governed-starter with source-backed frequency and loudly-caveated impact bridges

## In Progress

The decision engine is partially sketched but not fully integrated. The repository includes early control objects for frequency and impact reduction, a comparator, and orchestration notes. These pieces need cleanup before they should be treated as production-ready.

Emergent risk scenarios (AI-as-liability, correlated/systemic loss, governance/regulatory loss) are being built out per [docs/ROADMAP.md](ROADMAP.md), starting governed-starter and maturing as evidence deepens.

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

The command above runs every YAML scenario in `scenarios/`, prints portfolio statistics, saves a Loss Exceedance Curve to `results/`, and writes a JSON report when `--export` is included. The scenario folder mixes calibrated-workflow starters with older demo fixtures; see [scenarios/README.md](../scenarios/README.md) before treating portfolio output as decision-ready.

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

The console keeps all artifacts local and reviewable in `results/`. See [docs/CONSOLE_EXPERIENCE.md](CONSOLE_EXPERIENCE.md).

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
[docs/FX_RATE_REFRESH.md](FX_RATE_REFRESH.md)).

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

See [docs/CONSOLE_EXPERIENCE.md](CONSOLE_EXPERIENCE.md) for the guided
workflow and [CONTRIBUTING.md](../CONTRIBUTING.md) for the contribution path.
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

RiskShard does not currently apply heuristic contextual multipliers. To model a specific organization, generate an explicit calibrated scenario from reviewed evidence and simulate that scenario with the standard CLI. See [docs/org_specific_scenarios.md](org_specific_scenarios.md).

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

**And none of that is a statement about your context.** Fit exists only relative to a
target ([ADR-0011](adr/0011-fit-is-a-facet-set.md)), and the target on every published
surface is **our** shard cell, which is named wherever fit is rendered. Each parameter
prints two things: *declared for* — the population the source measured, a property of the
record and true for every reader — and *fit vs this cell*, which compares that population
against our target and tells you almost nothing about yours. Recompute the second from the
first; nothing else in the row moves. There is no fit score, grade or percentage, and there
will not be one: compressing those facets into a number would assert that a geography
mismatch and a size mismatch trade off in a way we cannot know for your scenario.

That the first line means what it says is a **repair, not an assumption**. On 2026-08-14,
**21 of 141 records** were found declaring the cell they were borrowed *for* rather than the
population measured — a US BEC frequency floor declaring financial-services mid-market over
an economy-wide numerator and denominator, three US frequencies declaring `US` over a UK
survey, two Singapore anchors declaring `SG` over US data. All 21 were corrected, **no
published figure moved**, and a test now fails the build if another appears
([finding 5](FINDINGS.md)).

**And cell-matched does not mean coherent.** A second, independent axis
([ADR-0007](adr/0007-construct-coherence.md), added 2026-08-07 after a practitioner
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
([ADR-0008](adr/0008-the-governed-tail.md), accepted 2026-08-07): every `impact.max` now
declares *what is known about it being exceeded*. Portfolio-wide, **4 of 11 maxima carry an
exceedance statement — 2 are modeled quantiles, 2 are observed ranks (1 of 579 claims, 1 of
84), 2 are legal ceilings, and 5 carry nothing at all.** That is not a footnote: in
[the worked decision](WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) the per-event mean runs
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
