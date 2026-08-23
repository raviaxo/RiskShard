# ADR-0006 — Depth over breadth

- **Status:** Accepted (2026-07-31); **scope narrowed 2026-08-15 by
  [ADR-0016](0016-the-audit-is-the-product.md) part 2** — shard coverage is frozen at 11 and the
  *Revisit when* section below no longer reopens breadth; **amended 2026-08-22** to state the axis
  and supply the measure this decision never had (see *Amendment*, below). The decision itself is
  unchanged and still binding.
- **Date:** 2026-07-31
- **Deciders:** repo owner
- **Related:** [`../internal/coverage_harvest.md`](../internal/coverage_harvest.md),
  [`../internal/canonical_reference_thesis.md`](../internal/canonical_reference_thesis.md),
  [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md)

## Context

Frequency evidence stopped being scarce on 2026-07-28. Eurostat `isoc_cisce_ic` carries
country- and size-specific incident rates for **35 countries** with a multi-year series, and
DORA supplies a supervisory per-entity rate for the EU financial sector. Either could seed
many new shards quickly.

`coverage_harvest.md` recorded the resulting question and deliberately did not answer it:
expand coverage, or stay deep? It gates most future evidence work, so it needed a decision
rather than a default.

## Decision

**Depth.** No new countries or sectors are added purely because the frequency data exists.
Effort goes to making existing shards more defensible.

## Reasoning

**The win condition rewards survivability, not coverage.** The strategy note
(`canonical_reference_thesis.md`) sets the goal as being *cited*, and a cited number has to
survive being attacked. Breadth does not help a single number withstand scrutiny.

**Breadth does not touch the binding constraint.** Impact is the constraint, and it is
shared. Adding twenty Eurostat countries produces twenty shards resting on the same bridged
impact side: `params_source_backed` would climb while nothing became more defensible. That is
precisely the failure mode [ADR-0003](0003-shared-impact-bridges.md) exists to expose.

**Eleven shards already exceed one maintainer's defence capacity.** The week of 2026-07-28
was spent almost entirely on defending and correcting the existing eleven — a stale-scenario
class defect across five of them, a portability bug in the seeds, a source that silently
rolled edition. Coverage added during that week would have multiplied the surface, not the
value.

**There is no demand signal.** Zero forks, zero Discussions, zero external contributors, and
no one has asked for a country. Coverage answers "is my cell here?", which is a question
nobody is currently asking, because the constraint is distribution rather than cell coverage.

## Consequences

- Eurostat and DORA remain **registered and available** (`evidence/third_party_outage.yaml`,
  `docs/internal/coverage_harvest.md`); this decision declines to *act* on them, it does not
  discard the research.
- Shard count stays flat for now, so it stops being a progress metric. The strength ledger
  and ADR-0003's cell-matched-vs-bridged split become the measures that matter.
- Contributor-facing coverage requests (`good first issue`, `docs/REQUESTED_SHARDS.md`) stay
  open: an *outside* request for a country is demand, and demand reopens this.

## Amendment — 2026-08-22: the axis, and the measure depth never had

Two things were left implicit here and have since misled a reader of this file alone.

### 1. The axis is depth on shards, breadth on sources

Nothing in this ADR was reversed. [ADR-0016](0016-the-audit-is-the-product.md) part 2 honoured it
by freezing shard coverage at 11 — *"depth over breadth was always the rule, and adding cells was
the drift"* — and ADR-0016 part 1 opened breadth on a **different object**: rows in a finite source
table, which is not the infinite parameter surface this ADR declined.

**What is withdrawn is this ADR's own trigger.** *Revisit when* below offers "a Discussion or issue
asking for a specific country or sector" as grounds to reopen. That is now false: ADR-0016 part 1
declines a new cell however it arrives, and `docs/REQUESTED_SHARDS.md` is no longer a route to one.
The remaining two triggers — a second maintainer, or genuinely per-cell impact evidence — survive,
because both change the constraint rather than the demand.

### 2. Depth was chosen without a live measure, and stayed that way for nine releases

The Decision commits effort to *"making existing shards more defensible"* and names no way to tell
whether it succeeded. The only candidate metric was `params_source_backed`, and it reached **66/66
on 2026-07-24** — a week before this ADR was accepted. It has read 66/66 in every one of the nine
releases since.

**That is a saturated metric, not stalled work**, and the distinction matters because the flat line
has already been misread once as evidence that this ADR stopped being followed. Over the same
window **10 commits touched `scenarios/` and 11 touched `calibrations/`** *(counted 2026-08-22 over
2026-07-31 → 2026-08-22; git history, so this is a dated measurement rather than a live figure)*.
The depth work happened. There was no instrument pointed at it.

**The measure it should have had is cell-matched**: how many parameters are drawn from the
population they are used for. It reads **7 of 66** ([finding 4](../FINDINGS.md)), it has 59 units of
headroom, and it cannot saturate while a single bridge remains.
`engine.cell_coverage.shard_self_coverage` now reports its distribution, which the corpus total hid:
**four shards hold all seven and seven shards hold none**, and no shard is complete on the cell it
is named after.

**This is a measure, not a target — and the difference is load-bearing.** ADR-0016 part 2 freezes
the shards as a demonstration, maintained for correctness only. Adopting cell-matched as a *goal*
would quietly reopen the shard investment that ADR-0016 closed, by the familiar route of making a
number visible and then wanting it to move. It is adopted here so the shards can **state** what
they rest on, per shard, which is a disclosure obligation. If it moves as a by-product of a source
correction, good. Work undertaken to move it needs ADR-0016 part 1's test first.

## Revisit when

Any one of: a Discussion or issue asking for a specific country or sector; a second
maintainer; or impact evidence that is genuinely per-cell rather than bridged, which would
make new shards defensible rather than merely numerous.

## Alternatives considered

- **Breadth-first**, using Eurostat to reach ~35 countries. Rejected: it multiplies a known
  weakness and inflates a metric that ADR-0003 shows cannot currently distinguish more
  evidence from more re-use of the same evidence.
- **Middle path** — expand only where a per-cell impact source exists. Rejected for now only
  because no such source has been found for any new cell; this becomes the natural path the
  moment one is.
