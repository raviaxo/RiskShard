# ADR-0003 — Shared, named impact bridges

- **Status:** Proposed
- **Date:** 2026-07-28
- **Deciders:** repo owner (this ADR records intent and a recommendation only)
- **Related:** [`../internal/coverage_harvest.md`](../internal/coverage_harvest.md),
  [`../internal/dora_prescout.md`](../internal/dora_prescout.md),
  [`../internal/es_availability_prescout.md`](../internal/es_availability_prescout.md),
  [`../METHODOLOGY.md`](../METHODOLOGY.md) (frequency/severity asymmetry)

## Context

Frequency evidence has become abundant. Eurostat `isoc_cisce_ic` carries country- and
size-specific incident rates for **35 countries**; DORA supplies a supervisory per-entity
rate for the EU financial sector. Neither existed in the repo a week ago.

Impact has gone the other way. Two independent scouting passes on 2026-07-28 both dead-ended:

- **Spanish national and regional bodies** (INCIBE, AEPD, Catalonia's agency, BCSC)
  publish incident **counts and typologies, essentially never euros**. AEPD publishes
  euros, but they are regulatory penalties, not event losses.
- **DORA mandates cost reporting** under Article 22(2) — and the first report found that
  half of major incidents reported no cost or under EUR 1,000, with a further 15% leaving
  the field blank, which the ESAs themselves flag as probable mis-reporting.

This is not bad luck. Per-country, per-sector, per-size loss-magnitude data mostly **does
not exist in public sources**, and there is no reason to expect it to appear. The engine
already says as much in `IMPACT_UNCERTAINTY_NOTE`: severity is far less predictable from a
shard's cell than frequency is.

Meanwhile the repo reports **66/66 parameters source-backed**. That is true in the sense
the label defines — every parameter traces to a named public source with a cited line and
a caveat. But several impact sides are the *same* generic cross-cyber loss research
(Cyentia IRIS medians, for instance) re-cited per shard, each with its own record and its
own caveat. A reader counting "66/66" reasonably infers more cell-specific evidence than
exists. The caveats are present and honest per record; the **aggregate impression** is not
as honest as the parts.

## Problem

Per-shard impact records imply a specificity the underlying evidence does not have, and
repeating a near-identical caveat across many records is a form of caveat dilution — the
eleventh restatement of "this is a generic cross-cyber bridge, not threat-specific" gets
skimmed. As shard count grows (and the frequency supply now permits rapid growth), this
gets worse, not better.

## Proposal

Introduce a first-class **impact bridge**: one named, sourced, versioned object that
several shards may explicitly reference, instead of each shard carrying its own copy.

- A bridge is declared once, with its source, cited line, derivation, and **one loud,
  carefully written limitations statement**.
- A shard's impact parameter either cites **cell-specific evidence** (as today) or
  **references a named bridge** — and which of the two it is becomes visible everywhere
  the parameter appears: explorer, provenance output, evidence report.
- Coverage reporting distinguishes the two. `params_source_backed` should no longer
  count a shared bridge as if it were cell-specific evidence.

### Consequences, including the uncomfortable one

**The headline number will fall.** Shards whose impact side rests on a shared bridge stop
counting as fully cell-specific, so "66/66 source-backed" becomes something like "N
cell-specific + M bridged". That is the point: the strength ledger currently cannot
distinguish *more evidence* from *more re-use of the same evidence*, and a metric that
cannot fall is not a measurement.

**It makes the weakness legible rather than distributed.** One bridge with one prominent
caveat is harder to skim past than eleven restatements, and a reader can see at a glance
how much of the portfolio leans on the same underlying study.

**It makes the correlation visible.** If eight shards share one impact bridge, their loss
figures are not independent. Nothing in the repo currently surfaces that, and it matters
for anyone aggregating across shards.

**It lowers the cost of a real improvement.** Replacing one bridge with better evidence
upgrades every shard referencing it, instead of requiring eleven separate edits.

## Alternatives considered

- **Do nothing.** Defensible: every individual record is already honest and caveated.
  Rejected because the aggregate claim drifts further from reality with every shard added,
  and the frequency supply now makes rapid addition easy.
- **Stop adding shards until per-cell impact data exists.** Rejected: the scouting says
  that data largely does not exist, so this is a permanent freeze on coverage.
- **Keep per-shard records but tag them as bridged.** A lighter version of this proposal
  and a reasonable fallback — it fixes the counting problem without the schema change,
  but leaves the caveat duplicated and the correlation invisible.

## Recommendation

Adopt, and take the headline drop deliberately and publicly — with a `revisions.yaml`
entry explaining it, the mechanism built on 2026-07-28 for exactly this kind of change.
A metric that goes down for a stated reason is more credible than one that only ever
goes up.

**Open questions for the owner:** whether bridges live in `evidence/` or a sibling
directory; whether an existing shard's impact records are migrated retroactively or only
new ones use bridges; and what the coverage tools should report as the headline number
once the two categories are distinguished.
