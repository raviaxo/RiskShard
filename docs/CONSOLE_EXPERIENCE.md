# RiskShard Console Experience

Last updated: 2026-06-15

The RiskShard console is a lightweight interactive shell for practitioners who want a guided workflow without leaving the CLI.

It is intentionally closer to a Metasploit-style console than a web app:

- Find available risk shards with `modules` or `search`.
- Inspect module metadata with `modules info <module-id>`.
- Inspect the machine-readable shard registry with `registry`.
- Inspect governed evidence packs with `packs <module-id>`.
- Select one with `use`.
- Inspect current location, selected shard, inputs, and next steps with `where` or `scenario`.
- Inspect global readiness with `readiness`.
- Run local setup/source/evidence/scenario/package checks with `doctor`.
- Get prioritized blockers and next commands with `next`.
- Inspect data-pack fingerprints with `pack`.
- Validate a proposed contribution pack with `preflight <pack-path>`.
- Scaffold a proposed contribution pack from the CLI with `python scripts/contributor_preflight.py scaffold ...`.
- Rank starter threats with `toprisks`.
- Explain missing or weak evidence with `show gaps`.
- Propose best available calibration selectors with `propose`.
- Generate an evidence-backed calibrated draft with `calibrate`.
- Simulate the selected or calibrated shard with `run`.
- Reset the selected shard and run state with `start over`.
- Inspect evidence, warnings, assumptions, gaps, and report artifacts with `show`.
- Summarize the latest calibration or run with `explain`.
- Run source/evidence quality gates with `validate`.

For Codex side-panel use, RiskShard also includes a local browser console
wrapper. It uses the same console commands and local files. It should not feel
like a separate fake application; every button runs a real console command.

The browser console now starts with the practitioner question:

```text
Given my company context, which Risk Shards can help me run and explain a cyber risk scenario?
```

The first screen is organized around:

- a short explanation of what a Risk Shard is;
- the current company context from the active/default org profile;
- available Risk Shards ranked by context fit and evidence coverage;
- selected Risk Shard actions for options, evidence, gaps, run, explain, and report;
- a concise trust boundary that distinguishes ready-to-run from benchmark-grade;
- contribution actions for country coverage and evidence improvement.
- registry actions that show the current shard-pack contract and catalog coverage.

The left command rail is independently scrollable so navigation stays available
while the console transcript and dashboard move. Expert users can still type any
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
riskshard> registry
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
riskshard(gb_finance_data_breach_midmarket)> where
riskshard(gb_finance_data_breach_midmarket)> scenario
riskshard(gb_finance_data_breach_midmarket)> show options
riskshard(gb_finance_data_breach_midmarket)> show gaps
riskshard(gb_finance_data_breach_midmarket)> propose
riskshard(gb_finance_data_breach_midmarket)> calibrate
riskshard(gb_finance_data_breach_midmarket)> show evidence
riskshard(gb_finance_data_breach_midmarket)> explain
riskshard(gb_finance_data_breach_midmarket)> run
riskshard(gb_finance_data_breach_midmarket)> report json
riskshard(gb_finance_data_breach_midmarket)> start over
```

For governed starter modules, `use` pre-fills the known org profile, calibration profile, and threat ID so a junior practitioner can reach a calibrated scenario quickly while still seeing every input.

The `countries` command shows the first 25 contribution geographies, including
seeded AU, US, and UK packs. `countries GB` also shows the UK coverage summary
and the next contributor gap.

## Risk Shard And Pack UX

Risk Shards live in `risk_modules/` and bind together the scenario, default
organization profile, calibration profile, evidence files, reviewed extractions,
and optional control profiles for a practitioner workflow.

The `registry` command summarizes those modules as a machine-readable contract:
module maturity, context coverage, evidence-pack status, consume/enhance
commands, and the expected contribution-pack layout.

Evidence packs are derived from those module descriptors. The `packs` command
shows direct parameter coverage, assumption-only parameters, source-backed
record counts, source gather timestamps, evidence ingestion dates, trust tiers,
confidence, renewal status, and renewal due dates.

The readiness dashboard still exposes detailed coverage, while the browser
console shows a simpler Risk Shard list. Each Risk Shard is summarized by:

```text
country / industry / company size / threat
source-backed direct parameters
pack confidence
next evidence gap
```

This keeps the browser console navigable without hiding the detailed evidence:
the `packs`, `propose`, `show gaps`, `readiness`, `feeds`, and `registry`
commands remain the source of truth for deeper review.

For contributors, the scaffold command writes a starter pack layout outside the
console:

```text
python scripts/contributor_preflight.py scaffold proposed_packs/ca_finance_data_breach_midmarket \
  --module-id ca_finance_data_breach_midmarket \
  --country CA \
  --industry financial_services \
  --company-size mid_market \
  --threat data_breach
```

The generated files contain explicit `REPLACE_ME` placeholders. Preflight warns
until those placeholders are replaced with reviewed source-backed content.

Scenario search and readiness output label each scenario as either `governed starter` or `demo fixture`. This keeps older smoke-test examples useful without making them look decision-ready.

## Design Rules

- Keep commands discoverable and boring.
- Keep outputs local, file-backed, and reviewable.
- Keep source-backed evidence, assumptions, warnings, and quality issues visible.
- Do not hide calibration uncertainty behind friendly copy.
- Do not expand the local browser wrapper into a hosted web UI, database, API service, optimizer, or chat surface as part of the console.

## Next Console Improvements

- Add clearer guidance for moving `calibrated_with_assumptions` shards to fully source-backed `calibrated` status.
- Add copyable run/calibration commands for selected shards.
- Add explicit company-context switching once multiple org profiles are ready.
- Add one-click source/feed details from each trust action.
