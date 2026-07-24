# RiskShard Documentation

New here? Read these first, in order:

1. [../README.md](../README.md) — what RiskShard is, the one-command demo, and honest status.
2. [METHODOLOGY.md](METHODOLOGY.md) — the quantitative model: how a loss number is computed, why Monte Carlo over a point estimate, the frequency/severity asymmetry, its limits, and the accountability stance.
3. [../CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute, including the DCO sign-off.

## Proof

- [BACKTEST_VALIDATION.md](BACKTEST_VALIDATION.md) — RiskShard checking its own frequency numbers against open incident data, and reporting what held and what didn't.

## Engineering

- [architecture.md](architecture.md) — current engine, evidence, calibration, and control architecture.
- [monte-carlo-determinism-architecture.md](monte-carlo-determinism-architecture.md) — reproducibility design (per-scenario seeding, fingerprints).
- [FX_RATE_REFRESH.md](FX_RATE_REFRESH.md) — how the sourced FX assumptions are refreshed.
- [org_specific_scenarios.md](org_specific_scenarios.md) — how organization profiles affect scenarios.
- [adr/](adr/) — architecture decision records (ADR-0001: loss-chain scenario modeling — conditional downstream loss stages).

## Direction

- [ROADMAP.md](ROADMAP.md) — emergent risk scenarios (AI-as-liability, correlated/systemic loss, governance/regulatory loss) and the loss-chain schema direction.

## Using and contributing

- [CONSOLE_EXPERIENCE.md](CONSOLE_EXPERIENCE.md) — the interactive console workflow and scope guardrails.
- [GOLDEN_CONTRIBUTOR_EXAMPLE.md](GOLDEN_CONTRIBUTOR_EXAMPLE.md) — a public source taken end-to-end (source → extraction → evidence → calibration → passing preflight).
- [BENCHMARK_CONTRIBUTOR_WORKFLOW.md](BENCHMARK_CONTRIBUTOR_WORKFLOW.md) — the content-pack, preflight, and evidence-pack workflow for contributors.
- [CONTENT_CONTRIBUTION.md](CONTENT_CONTRIBUTION.md) — per-artifact contributor checklists (source, extraction, evidence, calibration, module, country pack).

## Community

- [REQUESTED_SHARDS.md](REQUESTED_SHARDS.md) — what the community wants quantified next (the demand signal); how to request a shard.
- **Shard Notes** — the weekly build-in-public digest. Generate the skeleton with `python scripts/weekly_digest.py` (or `riskshard-weekly`): auto-fills state, what shipped, and contributors; you add the lesson and what's next. The digest also shows the strength delta since the last release, read from the progress ledger below.
- **Progress ledger** — the strength-over-time series. `python scripts/strength_ledger.py record` appends one snapshot per data-pack release (source-backed params, shards at 6/6, bridged/estimated counts, grades); it is a no-op unless the pack fingerprint changed, so the trend can't be padded. `python scripts/strength_ledger.py show` prints the latest release and its delta. The ledger (`docs/internal/strength_ledger.json`) is the canonical owner of the trend; the weekly digest reads it.
