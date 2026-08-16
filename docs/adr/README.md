# Architecture Decision Records

Strategic and architectural decisions for RiskShard, recorded so future work (human or
agent) can see *why* the system is shaped the way it is. Governed by
[`../PUBLISHABLE_REQUIREMENTS.md`](../PUBLISHABLE_REQUIREMENTS.md) → Change Control: a
schema, methodology, or maturity-definition change needs a recorded decision here first.

Each ADR is `NNNN-short-title.md`, numbered in order, with a status of **Proposed**,
**Accepted**, **Rejected**, or **Superseded**. A `Proposed` ADR records intent and a
recommendation; only the repo owner moves it to `Accepted`.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-loss-chain-scenario-modeling.md) | Loss-chain scenario modeling | Accepted |
| [0002](0002-portable-scenario-seed.md) | Portable scenario seeds (machine-independent simulation) | Accepted |
| [0003](0003-shared-impact-bridges.md) | Shared, named impact bridges | Accepted (parts 1–2); stored `population_match` superseded by 0013 |
| [0004](0004-citable-parameter-identifiers.md) | Citable parameter identifiers | Accepted |
| [0005](0005-documented-loss-event-registry.md) | Documented loss-event registry | Superseded by 0012 |
| [0006](0006-depth-over-breadth.md) | Depth over breadth | Accepted |
| [0007](0007-construct-coherence.md) | Declared measurement basis and range coherence | Proposed |
| [0008](0008-the-governed-tail.md) | The governed tail: a maximum must say what it bounds | Accepted |
| [0009](0009-what-riskshard-is-and-is-not.md) | What RiskShard is, and what it is not (scope) | Accepted |
| [0010](0010-where-riskshard-stops.md) | Where RiskShard stops: the evidence object is the product | Accepted |
| [0011](0011-fit-is-a-facet-set.md) | Fit is a facet set, not a score | Accepted (corrected 2026-08-14) |
| [0012](0012-loss-event-registry-bounded-trial.md) | The loss-event registry, as a bounded trial | Accepted |
| [0013](0013-fit-is-derived-not-stored.md) | Fit is derived against a target, not stored on the record | Accepted |
| [0014](0014-the-reader-supplies-the-target.md) | The reader supplies the target | Accepted |
| [0015](0015-the-source-audit.md) | The source audit: what a source publishes is not what we extracted | Accepted |
| [0016](0016-the-audit-is-the-product.md) | The source audit is the product; the shards are the demonstration | Accepted |
| [0017](0017-the-kill-criterion-gets-a-clock.md) | The kill criterion gets a clock, and this is the only time it moves | Accepted |
