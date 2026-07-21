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

As of 2026-07-21, the old P1/P2/P3 queue (BEC coverage, Insider/Third-Party evidence,
release discipline) is **cleared** — all BEC shards are source-backed, Insider Misuse and
Third-Party Outage are evidenced, and a data-pack release is cut. The dashboard now surfaces:

- **Add calibration profiles** for the three evidenced top-risk threats (`ai_enabled_fraud`,
  Insider Misuse, Third-Party Outage) — turning their 6/6 evidence into runnable shards.
- **Finish `jp_manufacturing_ransomware_midmarket`** (4/6 source-backed, 2 assumptions).
- **Emergent scenarios** from [`ROADMAP.md`](ROADMAP.md) (correlated vendor outage, EU AI Act
  penalty, regulatory enforcement), buildable as threats or ADR-0001 loss-chains.
- **Deferred/flagged:** `au_finance_data_breach_midmarket` under-labeled vs its gate; the
  README threat narrative is stale; Third-Party Outage `frequency.max` is a labeled estimate
  pending a directly reported figure.

The active work queue is [`NEXT_STEPS.md`](NEXT_STEPS.md); the live gap list is
`readiness_dashboard.py`.
