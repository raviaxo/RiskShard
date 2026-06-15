# RiskShard

RiskShard is an open-source engine for quantitative cyber risk analysis. It turns machine-readable risk scenarios into financial loss simulations so security, GRC, and risk teams can move from "high / medium / low" ratings toward defensible dollar-based decisions.

The current project is an early but functional Python prototype. It can run Monte Carlo simulations against YAML-defined scenarios, aggregate multiple scenarios into a portfolio view, generate summary statistics, export JSON reports, and produce Loss Exceedance Curve charts.

## Product Thesis

RiskShard aims to become a shared computation layer for cyber risk:

- Scenarios are stored as YAML "risk shards" that can be reviewed, versioned, reused, and generated.
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

See [docs/CODEX_REPO_REVIEW.md](docs/CODEX_REPO_REVIEW.md) for a concise technical review and cleanup list.

## Repository Layout

```text
AGENTS.md                Operating notes for future Codex sessions
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
docs/                    Vision, roadmap, architecture, and strategy notes
```

## Quick Start

```bash
git clone https://github.com/raviaxo/RiskShard.git
cd RiskShard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

Or start the local browser console for a Codex side-panel style workflow:

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
```

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

The calibration reports show a bottom line, confidence summary, what changed from the base scenario, limitations, selected evidence, applicable but excluded evidence, normalization assumptions, currency conversion assumptions, warnings, and the generated `frequency.min/likely/max` and `impact.min/likely/max` ranges. Current FX rates live in `calibrations/fx_rates.yaml`; the included AUD/USD rate is sourced from RBA Statistical Table F11.1 and inverted explicitly for USD-to-AUD calibration conversions, while GBP/USD coverage is recorded as an explicit ECB-derived cross-rate.

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

The feed inventory separates source publication date, source gather time, reviewed evidence ingestion date, trust tier, evidence confidence, renewal due date, and fetch status. See [docs/GLOBAL_READINESS_ROADMAP.md](docs/GLOBAL_READINESS_ROADMAP.md).

Inspect global readiness with:

```bash
python scripts/readiness_dashboard.py
```

The readiness view also exposes a gate and prioritized next actions so practitioners can see whether a shard is blocked, source-review-needed, assumption-review-needed, or ready for a local calibrated run.

Inspect the benchmark-grade 30 adoption program with:

```bash
python scripts/benchmark_program.py
python scripts/benchmark_program.py --cohort seeded
python scripts/benchmark_program.py --sprint seeded
python scripts/benchmark_program.py --target gb_finance_data_breach_midmarket
```

The benchmark program tracks thirty target shards and reports which ones are missing modules, which need evidence upgrades, and which are ready for human benchmark review. The seeded cohort view focuses on the five runnable modules, and the sprint view turns the next evidence-upgrade queue into target-level blockers, required artifacts, and review commands. It prevents starter shards from being overclaimed as benchmark-grade.

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

Provenance files live in `provenance/` and label every evidence record as `source_backed`, `estimated`, or `synthetic`. The canonical Australia finance ransomware example now uses public source-backed evidence for key frequency, impact, sector applicability, and regulatory context. Its range bounds still include estimated model assumptions, so the overall confidence remains low until better Australia-specific tail-loss evidence is added.

Taxonomies live in `taxonomies/` and are the vetted source for dropdown-style IDs such as `financial_services`, `AU`, `mid_market`, and `ransomware`.

Evidence records live in `evidence/`. They are separate from scenarios: evidence records capture extracted facts and applicability, while scenarios remain simulation-ready inputs. Evidence matching explains whether each record is an exact match or a fallback for the supplied organization profile and threat.

Risk modules live in `risk_modules/`. They do not change the simulation schema;
they describe the practitioner workflow around a shard: scenario, default
organization profile, calibration profile, evidence pack, reviewed extractions,
controls, tags, and what the module is or is not good for.

Source-backed evidence records should include `source_id` values that map to `sources/manifest.json`, plus a concise `citation_detail` describing where the fact appears in the source. Estimated or synthetic model assumptions must remain labeled as `estimated` or `synthetic`.

Reviewed extraction records live in `extractions/` and document the fact pulled from a source before it becomes one or more structured evidence records.

The starter threat library lives in `threat_library/`. Ransomware, data breach, and business email compromise now have Australia financial-services calibration profiles, but all still carry explicit assumption warnings. Data breach has DBIR/OAIC context evidence, a denominator-derived reported-breach frequency floor, and source-backed global impact anchors; its likely and stress frequency parameters remain estimated until stronger organization-level likelihood evidence is reviewed. Business email compromise has FBI IC3 source-backed likely-loss evidence and ACCC Australia small-business loss context; frequency and stress loss bounds remain estimated until denominator-aware BEC evidence is reviewed.

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

## Source Baseline

RiskShard can gather a curated baseline of public source materials and write an auditable manifest:

```bash
python scripts/gather_sources.py
```

The source registry lives in `sources/registry.yaml`. The generated manifest lives in `sources/manifest.json` and records each source's publication date, gather timestamp, final URL, HTTP status, content type, byte count, SHA-256 hash, and raw artifact path. Raw downloaded artifacts are stored under `sources/raw/` and ignored by Git.

Gathering a source does not automatically make it a benchmark parameter. Extracted facts should still be reviewed and stored as evidence records with applicability, confidence, limitations, and honest evidence-type labels.

## Documentation Map

For the current documentation map, start with [docs/README.md](docs/README.md). The most important operational docs are:

- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/CONSOLE_EXPERIENCE.md](docs/CONSOLE_EXPERIENCE.md)
- [docs/GLOBAL_READINESS_ROADMAP.md](docs/GLOBAL_READINESS_ROADMAP.md)
- [docs/COUNTRY_EXPANSION.md](docs/COUNTRY_EXPANSION.md)
- [docs/MAJOR_MILESTONES.md](docs/MAJOR_MILESTONES.md)

## Current Strategic Questions

- Who is the first serious user: solo security leader, GRC analyst, risk consultant, AI agent builder, or platform vendor?
- Is the durable asset the simulation engine, the scenario library, the benchmark data model, or the AI-consumable risk API?
- How should benchmark sources, assumptions, and confidence levels be represented so outputs are defensible?
- What is the right path from CLI prototype to useful product: package, API service, web UI, or data repository first?
- How open should the parameter library be, and what governance model would make contributors trust it?

## License

RiskShard is released under the MIT License.
