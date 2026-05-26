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
- Early benchmark-to-scenario generation helpers
- Contextual single-scenario analysis using separate organization, control, and provenance inputs
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
library/benchmarks/      Benchmark source data and shard generation helper
library/adapters/        Adapter/helper experiments
scenarios/               Example YAML risk shards
schemas/                 JSON Schema for scenario validation
scripts/                 Thin CLI entry point
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

The command above runs every YAML scenario in `scenarios/`, prints portfolio statistics, saves a Loss Exceedance Curve to `results/`, and writes a JSON report when `--export` is included.

## Contextual Analysis

RiskShard can also run one scenario against separate organization, control, and provenance inputs:

```bash
python scripts/fair_calc.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --control-profile control_profiles/ransomware_basic_controls.yaml \
  --provenance provenance/au_finance_ransomware_midmarket.yaml \
  --threat ransomware \
  --evidence evidence \
  --trials 10000 \
  --dist pert \
  --seed 42 \
  --report-output results/au_finance_ransomware_contextual.json
```

The contextual report is JSON and includes scenario parameters, organization context, control context, explicit assumptions, provenance records, evidence match rationale, confidence, baseline results, control-adjusted results, and delta.

The current contextual multipliers are minimal estimated heuristics. They are labeled as estimated in the report and should be replaced with benchmark-backed calibration before real decision support.

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

## Context Input Files

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

Control profiles live in `control_profiles/` and remain transformations over the scenario, not embedded scenario properties.

Provenance files live in `provenance/` and label every evidence record as `source_backed`, `estimated`, or `synthetic`. The canonical Australia finance ransomware example now uses public source-backed evidence for key frequency, impact, sector applicability, and regulatory context. Its range bounds still include estimated model assumptions, so the overall confidence remains low until better Australia-specific tail-loss evidence is added.

Taxonomies live in `taxonomies/` and are the vetted source for dropdown-style IDs such as `financial_services`, `AU`, `mid_market`, and `ransomware`.

Evidence records live in `evidence/`. They are separate from scenarios: evidence records capture extracted facts and applicability, while scenarios remain simulation-ready inputs. Evidence matching explains whether each record is an exact match or a fallback for the supplied organization profile and threat.

## Strategy Docs

For strategy brainstorming, start with:

- [docs/CHATGPT_STRATEGY_BRIEF.md](docs/CHATGPT_STRATEGY_BRIEF.md)
- [docs/CODEX_REPO_REVIEW.md](docs/CODEX_REPO_REVIEW.md)
- [docs/roadmap.md](docs/roadmap.md)
- [docs/vision.md](docs/vision.md)

## Current Strategic Questions

- Who is the first serious user: solo security leader, GRC analyst, risk consultant, AI agent builder, or platform vendor?
- Is the durable asset the simulation engine, the scenario library, the benchmark data model, or the AI-consumable risk API?
- How should benchmark sources, assumptions, and confidence levels be represented so outputs are defensible?
- What is the right path from CLI prototype to useful product: package, API service, web UI, or data repository first?
- How open should the parameter library be, and what governance model would make contributors trust it?

## License

RiskShard is released under the MIT License.
