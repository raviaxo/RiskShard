# RiskShard Console Experience

Last updated: 2026-06-04

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
- Rank starter threats with `toprisks`.
- Explain missing or weak evidence with `show gaps`.
- Propose best available calibration selectors with `propose`.
- Generate an evidence-backed calibrated draft with `calibrate`.
- Simulate the selected or calibrated shard with `run`.
- Inspect evidence, warnings, assumptions, gaps, and report artifacts with `show`.
- Summarize the latest calibration or run with `explain`.
- Run source/evidence quality gates with `validate`.

For Codex side-panel use, RiskShard also includes a local browser console wrapper. It uses the same console commands and local files, but presents them as buttons plus a command input:

```text
python scripts/riskshard_web_console.py
```

## First Workflow

```text
python scripts/riskshard_console.py
riskshard> workflow
riskshard> toprisks
riskshard> modules
riskshard> modules info au_finance_ransomware_midmarket
riskshard> packs au_finance_ransomware_midmarket
riskshard> doctor
riskshard> readiness
riskshard> next
riskshard> feeds
riskshard> pack
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

For governed starter modules, `use` pre-fills the known org profile, calibration profile, and threat ID so a junior practitioner can reach a calibrated scenario quickly while still seeing every input.

## Module And Pack UX

Risk modules live in `risk_modules/` and bind together the scenario, default
organization profile, calibration profile, evidence files, reviewed extractions,
and optional control profiles for a practitioner workflow.

Evidence packs are derived from those module descriptors. The `packs` command
shows direct parameter coverage, assumption-only parameters, source-backed
record counts, source gather timestamps, evidence ingestion dates, trust tiers,
confidence, renewal status, and renewal due dates.

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
