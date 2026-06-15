# RiskShard Console Experience

Last updated: 2026-06-15

The RiskShard console is a lightweight interactive shell for practitioners who want a guided workflow without leaving the CLI.

It is intentionally closer to a Metasploit-style console than a web app:

- Find available risk shards with `modules` or `search`.
- Inspect module metadata with `modules info <module-id>`.
- Inspect governed evidence packs with `packs <module-id>`.
- Select one with `use`.
- Inspect ranges and context with `info` and `show options`.
- Inspect global readiness with `readiness`.
- Run local setup/source/evidence/scenario/package checks with `doctor`.
- Get prioritized blockers and next commands with `next`.
- Inspect data-pack fingerprints with `pack`.
- Validate a proposed contribution pack with `preflight <pack-path>`.
- Rank starter threats with `toprisks`.
- Explain missing or weak evidence with `show gaps`.
- Propose best available calibration selectors with `propose`.
- Generate an evidence-backed calibrated draft with `calibrate`.
- Simulate the selected or calibrated shard with `run`.
- Inspect evidence, warnings, assumptions, gaps, and report artifacts with `show`.
- Summarize the latest calibration or run with `explain`.
- Run source/evidence quality gates with `validate`.

For Codex side-panel use, RiskShard also includes a local browser console
wrapper. It uses the same console commands and local files, but organizes the
first screen into four practitioner lanes:

- Run a shard
- Improve evidence
- Govern data
- Contribute country

The dashboard then exposes contextual actions for the selected module, so users
do not have to parse every command at once. Expert users can still type any
console command in the input.

```text
python scripts/riskshard_web_console.py
```

## First Workflow

```text
python scripts/riskshard_console.py
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
riskshard> pack
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

For governed starter modules, `use` pre-fills the known org profile, calibration profile, and threat ID so a junior practitioner can reach a calibrated scenario quickly while still seeing every input.

The `countries` command shows the first 25 contribution geographies, including
seeded AU, US, and UK packs. `countries GB` also shows the UK coverage summary
and the next contributor gap.

## Module And Pack UX

Risk modules live in `risk_modules/` and bind together the scenario, default
organization profile, calibration profile, evidence files, reviewed extractions,
and optional control profiles for a practitioner workflow.

Evidence packs are derived from those module descriptors. The `packs` command
shows direct parameter coverage, assumption-only parameters, source-backed
record counts, source gather timestamps, evidence ingestion dates, trust tiers,
confidence, renewal status, and renewal due dates.

The readiness dashboard and browser console now include a module coverage
matrix. Each module is shown with the six direct parameters:

```text
frequency.min / frequency.likely / frequency.max
impact.min / impact.likely / impact.max
```

Each cell is labeled source-backed, assumption-only, or missing. This is the
main UX affordance for deciding what evidence to improve next. In the browser
console, source-backed cells open the module evidence pack, while
assumption-only or missing cells open the calibration proposal for that module.
Each module row also exposes Use, Pack, and Fix gap actions.

Scenario search and readiness output label each scenario as either `governed starter` or `demo fixture`. This keeps older smoke-test examples useful without making them look decision-ready.

## Design Rules

- Keep commands discoverable and boring.
- Keep outputs local, file-backed, and reviewable.
- Keep source-backed evidence, assumptions, warnings, and quality issues visible.
- Do not hide calibration uncertainty behind friendly copy.
- Do not expand the local browser wrapper into a hosted web UI, database, API service, optimizer, or chat surface as part of the console.

## Next Console Improvements

- Add clearer guidance for moving `calibrated_with_assumptions` shards to fully source-backed `calibrated` status.
- Add one-click source/feed details from each dashboard action.
- Add copyable run/calibration commands for selected shards.
- Add beginner/expert display mode if the four-lane layout is still too dense.
