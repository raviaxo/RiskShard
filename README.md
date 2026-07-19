# RiskShard

**The open, evidence-governed computation layer for cyber risk quantification.**

RiskShard turns machine-readable "risk shards" into financial loss simulations, so
security, GRC, and risk teams can move from "high / medium / low" ratings to
defensible, dollar-based decisions — with every number traceable to a reviewed
public source. Think of it as a Metasploit-style module library for risk
quantification: pick a shard, see how much to trust it, run it, improve it.

## The question RiskShard answers

> Given my geography, industry, company size, and threat concern: which risk
> scenarios apply, how much should I trust them, what loss range do they imply,
> and how do I improve the data?

You select a Risk Shard (say, a UK financial-services data breach), inspect which
parameters are source-backed versus assumptions, run a Monte Carlo loss
simulation, get a board-ready summary, and see the next evidence gap to close.

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

## Honest status

RiskShard is a working practitioner beta, not a finished product. Shards are
labeled by maturity: `governed_starter`, automated `benchmark_candidate`, and —
only after a recorded human review decision — benchmark-grade. "Automated
benchmark-ready" is never the same as "human-approved benchmark-grade," and the
distinction stays visible everywhere results appear.

## See the proof

Two artifacts show what "evidence-governed" buys you in practice.

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
- Risk module catalog for Metasploit-style `modules`, `info`, `use`, `packs`, `propose`, `calibrate`, and `run` workflows
- Evidence-pack registry that shows source gather dates, evidence ingestion dates, trust tier, confidence, renewal status, and remaining assumptions per module
- Country expansion priority map covering 25 countries so regional contributors can pick high-value evidence packs
- Reviewed source-to-extraction-to-evidence-to-calibration workflow
- Governed starter vs demo fixture labels in scenario metadata, CLI output, readiness, and console search
- Vetted YAML taxonomies and evidence matching for industry, country, company size, and threat context

## In Progress

The decision engine is partially sketched but not fully integrated. The repository includes early control objects for frequency and impact reduction, a comparator, and orchestration notes. These pieces need cleanup before they should be treated as production-ready.

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

## Evidence Calibration

RiskShard can generate a draft calibrated scenario from reviewed evidence:

```bash
python scripts/calibrate_scenario.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --evidence evidence \
  --calibration calibrations/au_finance_ransomware.yaml \
  --threat ransomware \
  --report-output results/au_finance_ransomware_calibration.json \
  --markdown-output results/au_finance_ransomware_calibration.md \
  --scenario-output results/au_finance_ransomware_calibrated.yaml
```

The calibration reports show a bottom line, confidence summary, what changed from the base scenario, limitations, selected evidence, applicable but excluded evidence, normalization assumptions, currency conversion assumptions, warnings, and the generated `frequency.min/likely/max` and `impact.min/likely/max` ranges. Current FX rates live in `calibrations/fx_rates.yaml`; the included AUD/USD rate is sourced from RBA Statistical Table F11.1 and inverted explicitly for USD-to-AUD calibration conversions, GBP/USD coverage is recorded as an explicit ECB-derived cross-rate, and USD/CAD coverage is recorded as an explicit Bank of Canada FXUSDCAD rate.

Validate evidence quality gates with:

```bash
python scripts/validate_evidence.py
```

Refresh static FX assumptions with:

```bash
python scripts/update_fx_rates.py --output calibrations/fx_rates.yaml
```

See [docs/FX_RATE_REFRESH.md](docs/FX_RATE_REFRESH.md) for the review checklist.

Inspect data feed governance with:

```bash
python scripts/data_governance.py
```

The feed inventory separates source publication date, source gather time, reviewed evidence ingestion date, trust tier, evidence confidence, renewal due date, and fetch status.

Inspect global readiness with:

```bash
python scripts/readiness_dashboard.py
```

The readiness view also exposes a gate and prioritized next actions so practitioners can see whether a shard is blocked, source-review-needed, assumption-review-needed, or ready for a local calibrated run.

Inspect stricter beta readiness before expanding public operations with:

```bash
python scripts/beta_readiness.py
```

The beta gate is intentionally stricter than local run readiness. It checks
module depth, benchmark-ready candidates, source/evidence health, package smoke,
data-pack fingerprinting, minimum governance docs, and clean-install proof.

Refresh the clean-install proof from a fresh local virtual environment with:

```bash
python scripts/clean_install_proof.py --recreate
```

Inspect the benchmark-grade 30 adoption program with:

```bash
python scripts/benchmark_program.py
python scripts/benchmark_program.py --cohort seeded
python scripts/benchmark_program.py --sprint seeded
python scripts/benchmark_program.py --target gb_finance_data_breach_midmarket
```

The benchmark program tracks thirty target shards and reports which ones are missing modules, which need evidence upgrades, and which are ready for human benchmark review. The seeded cohort view focuses on the ten runnable modules, and the sprint view turns the next evidence-upgrade queue into target-level blockers, required artifacts, and review commands. It prevents starter shards from being overclaimed as benchmark-grade.

Rank starter threats by evidence and calibration readiness with:

```bash
python scripts/riskshard_toprisks.py --limit 5
python scripts/riskshard_toprisks.py --json
```

Inspect risk modules and evidence packs with:

```bash
python scripts/riskshard_modules.py list
python scripts/riskshard_modules.py info gb_finance_data_breach_midmarket
python scripts/riskshard_modules.py packs gb_finance_data_breach_midmarket
python scripts/riskshard_modules.py packs gb_finance_data_breach_midmarket --export results/gb_breach_evidence_pack.json
python scripts/riskshard_modules.py propose gb_finance_data_breach_midmarket
```

Risk modules are the current Metasploit-style front door: they bind a scenario,
organization profile, calibration profile, evidence files, extraction files,
control profiles, and governed source feeds into one searchable unit.
The `--export` path writes a local module evidence-pack artifact with a
fingerprint and SHA-256 hashes for the module's review files.

Inspect the country contribution roadmap with:

```bash
python scripts/riskshard_modules.py countries
python scripts/riskshard_modules.py countries US
python scripts/riskshard_modules.py countries GB
```

Run the local doctor with:

```bash
python scripts/riskshard_doctor.py
python scripts/riskshard_doctor.py --run-tests
```

The doctor combines environment, source, evidence, extraction, scenario-stage, readiness, package entry-point smoke, data-pack, and test-readiness checks.

Verify declared package commands directly with:

```bash
python scripts/package_smoke.py
```

Generate a data-pack fingerprint for governed inputs with:

```bash
python scripts/data_pack_manifest.py
```

Cut a named local data-pack release artifact with:

```bash
python scripts/data_pack_manifest.py --release 2026.06.15
```

The release artifact is written under `data_pack_releases/` and includes the
pack fingerprint plus the governed file manifest so scenario reviews can pin
the exact source/evidence/calibration state.

Run contributor preflight for the current checkout or for a proposed content
pack directory:

```bash
python scripts/contributor_preflight.py
python scripts/contributor_preflight.py path/to/proposed_pack
```

For proposed packs, preflight checks source registry entries, evidence records,
reviewed extractions, calibration selectors, risk-module artifacts, and pack
notes before a pull request. It also warns when a proposed module does not map
to the Benchmark-Grade 30 roadmap. See
[docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md](docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md).

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

The starter threat library lives in `threat_library/`. Ransomware, data breach, and business email compromise now have Australia financial-services calibration profiles. Ransomware has six source-backed direct selectors and is ready for human benchmark review. Data breach has DBIR/OAIC context evidence, a denominator-derived reported-breach frequency floor, official UK breach/attack prevalence bridges for likely and stress frequency, an Australian medium-business cybercrime cost floor, an IBM UK financial-services likely-impact bridge, and an Australian Privacy Act penalty-cap stress anchor; it is now an automated benchmark-review candidate, but still needs human caveat review before public benchmark-grade claims. Business email compromise has FBI IC3 source-backed likely-loss evidence and ACCC Australia small-business loss context; frequency and stress loss bounds remain estimated until denominator-aware BEC evidence is reviewed.

The first second-geography module is `us_finance_bec_midmarket`. It uses FBI IC3
source-backed likely-loss evidence and keeps US BEC frequency/floor/tail
assumptions explicit until US denominator-aware evidence is contributed.

The next seeded geography is `gb_finance_data_breach_midmarket`. It uses UK
official cyber breach/attack prevalence for frequency and IBM UK financial
services data-breach cost evidence for likely impact. Its stress impact uses an
FCA Equifax cyber-breach penalty anchor, so all six direct parameters are now
source-backed. It is still a governed starter, not benchmark-grade: the UK
survey is broader than privacy-only data breach, and the stress anchor is a
regulatory penalty rather than a total event-loss or claims distribution.

Canada is seeded through `ca_finance_data_breach_midmarket`. It uses OPC/CIRA
Canadian prevalence anchors for frequency min/likely and expresses impact in
CAD. It now clears the automated benchmark gate: all six direct parameters are
source-backed and extraction-mapped. It is still a benchmark-review candidate,
not a public benchmark-grade claim, because impact min/likely/max use primary
global loss anchors converted with a Bank of Canada FX assumption until primary
Canada-specific impact evidence is gathered.

Germany industrial ransomware is now an automated benchmark-review candidate.
It uses Bitkom Germany ransomware frequency anchors, a Germany ransom-payment
impact floor with explicit EUR/USD conversion, and Sophos manufacturing
ransomware impact bridges. It is not a public benchmark-grade claim until human
review accepts those caveats.

Singapore finance BEC, Japan manufacturing ransomware, and France finance data
breach remain governed starter modules. They are contribution scaffolds with
transparent assumptions and global anchors, not benchmark-grade local models.

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

## Current Strategic Questions

- Who is the first serious user: solo security leader, GRC analyst, risk consultant, AI agent builder, or platform vendor?
- Is the durable asset the simulation engine, the scenario library, the benchmark data model, or the AI-consumable risk API?
- How should benchmark sources, assumptions, and confidence levels be represented so outputs are defensible?
- What is the right path from CLI prototype to useful product: package, API service, web UI, or data repository first?
- How open should the parameter library be, and what governance model would make contributors trust it?

## License

Copyright (C) 2026 Sergio Alonso.

RiskShard is free software, licensed under the **GNU Affero General Public License
v3.0 (AGPL-3.0)**. You may use, study, share, and modify it under those terms; if
you run a modified version as a network service, the AGPL requires you to offer
that service's users the corresponding source. See [LICENSE](LICENSE).

Contributions are accepted under the same license via the Developer Certificate of
Origin (DCO) — sign off your commits with `git commit -s`. See
[CONTRIBUTING.md](CONTRIBUTING.md).
