# RiskShard Documentation Map

**Session loop:** open with `/session:start`, close with `/session:end`. The live
handoff is three files, each the single owner of its fact — **Now** (current
priority + top blocker) → [HANDOVER_STOPPING_POINT.md](HANDOVER_STOPPING_POINT.md)
· **State** (capabilities, gaps) → [PROJECT_STATUS.md](PROJECT_STATUS.md) ·
**Next** (backlog) → [NEXT_STEPS.md](NEXT_STEPS.md).

**New here? Read only these three, in order — everything else is reference you can reach for when you need it:**

1. [../README.md](../README.md): what RiskShard is, the one-command demo, and honest status.
2. [PROJECT_STATUS.md](PROJECT_STATUS.md): current capabilities, known gaps, and definition of done.
3. [NEXT_STEPS.md](NEXT_STEPS.md): the prioritized backlog — what is being worked on now.

Contributing a shard? Add [CONTRIBUTING.md](CONTRIBUTING.md) and
[GOLDEN_CONTRIBUTOR_EXAMPLE.md](GOLDEN_CONTRIBUTOR_EXAMPLE.md). That is the whole
starting path; the sections below are for when a specific question sends you there.

## Canonical state, governance, and process (by need)

- [PUBLISHABLE_REQUIREMENTS.md](PUBLISHABLE_REQUIREMENTS.md): controlling phase requirements, public launch bar, community operating model, and strategic change-control rules.
- [HANDOVER_STOPPING_POINT.md](HANDOVER_STOPPING_POINT.md): precise restart file for the next Codex or harness session, including current blocker and resume order.
- [PUBLIC_READINESS_8H_SESSION.md](PUBLIC_READINESS_8H_SESSION.md): current public-readiness execution plan for the active work session.
- [USER_AUDIT_CHECKPOINT.md](USER_AUDIT_CHECKPOINT.md): usability, trust, contributor, practitioner, and executive-readiness checkpoint before further buildout.
- [BENCHMARK_REVIEW_LEDGER.md](BENCHMARK_REVIEW_LEDGER.md): human review ledger for automated benchmark candidates and release caveats.
- [SEEDED_EVIDENCE_UPGRADE_QUEUE.md](SEEDED_EVIDENCE_UPGRADE_QUEUE.md): ordered evidence-upgrade queue for seeded modules that are not yet benchmark-ready.
- [BENCHMARK_CONTRIBUTOR_WORKFLOW.md](BENCHMARK_CONTRIBUTOR_WORKFLOW.md): benchmark target, content-pack, preflight, and evidence-pack export workflow.
- [CONSOLE_EXPERIENCE.md](CONSOLE_EXPERIENCE.md): intended local console workflow and scope guardrails.
- [GLOBAL_READINESS_ROADMAP.md](GLOBAL_READINESS_ROADMAP.md): what global coverage and governance still require.
- [COUNTRY_EXPANSION.md](COUNTRY_EXPANSION.md): 25-country contribution priority map and second-geography plan.
- [MAJOR_MILESTONES.md](MAJOR_MILESTONES.md): major product and governance milestones.
- [BETA_KIT.md](BETA_KIT.md): ready-to-use public-share assets (LinkedIn post, DM, async intake, monthly Shard Spotlight template).
- [S1_BACKTEST_POC_PLAN.md](S1_BACKTEST_POC_PLAN.md): approved spec for the Lane 2 backtesting proof-of-concept (VCDB frequency-only, S2 gate) that precedes the public post.
- [S1_BACKTEST_FINDING.md](S1_BACKTEST_FINDING.md): the S1 backtest result (GB/US finance data-breach frequency vs. VCDB) and the pending S2 decision.

## Engineering detail

- [METHODOLOGY.md](METHODOLOGY.md): the quantitative model — how a loss number is computed, why Monte Carlo over a point estimate, the frequency/severity asymmetry, limits, and the accountability stance (Roadmap Lane 1 / F1).
- [architecture.md](architecture.md): current engine, evidence, calibration, and control architecture.
- [org_specific_scenarios.md](org_specific_scenarios.md): how organization profiles should affect scenarios.
- [FX_RATE_REFRESH.md](FX_RATE_REFRESH.md): sourced FX assumption refresh workflow.
- [monte-carlo-determinism-architecture.md](monte-carlo-determinism-architecture.md): reproducibility design notes and remaining determinism work.

## Historical and strategy context (not the active backlog)

- [GROWTH_AUDIT_REVIEW.md](GROWTH_AUDIT_REVIEW.md): growth guardrail review.
- [CODEX_REPO_REVIEW.md](CODEX_REPO_REVIEW.md): historical repo review from the first cleanup pass.
- [CHATGPT_STRATEGY_BRIEF.md](CHATGPT_STRATEGY_BRIEF.md): strategy brainstorming prompts.
- [roadmap.md](roadmap.md), [vision.md](vision.md), and [manifest.md](manifest.md): early product-direction notes superseded by the publishable requirements file for active execution.
