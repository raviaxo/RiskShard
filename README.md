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
riskshard> modules info au_finance_ransomware_midmarket
riskshard> packs au_finance_ransomware_midmarket
riskshard> doctor
riskshard> readiness
riskshard> next
riskshard> feeds
riskshard> use au_finance_ransomware_midmarket
riskshard(au_finance_ransomware_midmarket)> show options
riskshard(au_finance_ransomware_midmarket)> show gaps
riskshard(au_finance_ransomware_midmarket)> propose
riskshard(au_finance_ransomware_midmarket)> calibrate
riskshard(au_finance_ransomware_midmarket)> show evidence
riskshard(au_finance_ransomware_midmarket)> explain
riskshard(au_finance_ransomware_midmarket)> run
riskshard(au_finance_ransomware_midmarket)> report json
```

The console keeps all artifacts local and reviewable in `results/`. See [docs/CONSOLE_EXPERIENCE.md](docs/CONSOLE_EXPERIENCE.md).

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

The calibration reports show a bottom line, confidence summary, what changed from the base scenario, limitations, selected evidence, applicable but excluded evidence, normalization assumptions, currency conversion assumptions, warnings, and the generated `frequency.min/likely/max` and `impact.min/likely/max` ranges. Current FX rates live in `calibrations/fx_rates.yaml`; the included AUD/USD rate is sourced from RBA Statistical Table F11.1 and inverted explicitly for USD-to-AUD calibration conversions.

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

Inspect risk modules and evidence packs with:

```bash
python scripts/riskshard_modules.py list
python scripts/riskshard_modules.py info au_finance_ransomware_midmarket
python scripts/riskshard_modules.py packs au_finance_ransomware_midmarket
python scripts/riskshard_modules.py propose au_finance_ransomware_midmarket
```

Risk modules are the current Metasploit-style front door: they bind a scenario,
organization profile, calibration profile, evidence files, extraction files,
control profiles, and governed source feeds into one searchable unit.

Run the local doctor with:

```bash
python scripts/riskshard_doctor.py
python scripts/riskshard_doctor.py --run-tests
```

The doctor combines environment, source, evidence, extraction, scenario-stage, readiness, package entry-point, data-pack, and test-readiness checks.

Generate a data-pack fingerprint for governed inputs with:

```bash
python scripts/data_pack_manifest.py
```

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

## Current Strategic Questions

- Who is the first serious user: solo security leader, GRC analyst, risk consultant, AI agent builder, or platform vendor?
- Is the durable asset the simulation engine, the scenario library, the benchmark data model, or the AI-consumable risk API?
- How should benchmark sources, assumptions, and confidence levels be represented so outputs are defensible?
- What is the right path from CLI prototype to useful product: package, API service, web UI, or data repository first?
- How open should the parameter library be, and what governance model would make contributors trust it?

## License

RiskShard is released under the MIT License.
