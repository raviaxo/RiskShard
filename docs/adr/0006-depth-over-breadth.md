# ADR-0006 — Depth over breadth

- **Status:** Accepted
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
