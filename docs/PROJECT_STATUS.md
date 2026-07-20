# PROJECT_STATUS — capabilities and known gaps

This is a thin status pointer, not a second source of truth. It names the canonical
owners and records the current gaps. For anything that drifts, run the tool.

## Current capabilities

The canonical capability list is the **[README](../README.md)** — see "What Works
Today" and "In Progress". Do not duplicate it here; update the README instead.

For a live, generated view of coverage and health, run:

```bash
python scripts/readiness_dashboard.py     # coverage, gate, next actions
python scripts/riskshard_modules.py coverage   # data-strength grade per shard
python scripts/riskshard_doctor.py        # environment + data health
```

## Maturity ladder (claim discipline)

A shard's grade is data strength, not benchmark status:

- `governed_starter` — transparent assumptions / global bridges; directional only.
- `benchmark_candidate` / `benchmark_review_candidate` — clears the automated gate.
- **benchmark-grade** — only after a recorded human review decision. Never implied
  by automation.

## Known gaps (snapshot — the live list is `readiness_dashboard.py`)

As of 2026-07-20, the dashboard's prioritized next actions are:

- **P1 — Business Email Compromise coverage.** The US BEC shard is now 6/6
  source-backed (see `docs/NEXT_STEPS.md`, Objective 1); the AU and SG BEC shards
  still carry frequency assumptions, so BEC remains the library's soft spot.
- **P2 — Insider Misuse and Third-Party Outage** have missing direct evidence
  (partially supported).
- **P3 — Release discipline:** cut a named, fingerprinted data-pack release.

The active work queue that turns these gaps into sessions is
[`NEXT_STEPS.md`](NEXT_STEPS.md).
