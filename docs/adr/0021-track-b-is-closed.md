# ADR-0021 — Track B is closed, and the defect it existed for is left standing in the open

**Status: Accepted** (2026-09-27)

## Context

The roadmap has carried two tracks since 2026-08-19. Track A — the audit — finishes, and
[M1 closed on 2026-09-27](../ROADMAP.md). Track B — usability — was capped rather than planned,
one item at a time, each needing its own decision before it started.

**Track B has nothing left in it, and that happened by measurement rather than by neglect.**

- **U1 shipped** on 2026-08-22: every published figure states what it rests on.
- **U2 was declined** on 2026-08-23 by [ADR-0019](0019-borrowing-cannot-answer-an-unpublished-cell.md),
  on its own stated failure condition: nearest-shard borrowing would have turned 456 unanswerable
  cells into 456 relabelled copies of 11 numbers, with 59% of donors chosen by a tiebreak carrying
  no evidentiary meaning.
- **Everything after U2 depended on U2.** `execution_plan.md` sequenced W4 (borrowing), then W5
  (reader context) gated on W4, then W6 (UI) gated on W5. Declining W4 voided the chain, and the
  plan has said so since 2026-08-24 without anyone deciding what replaced it.

So for five weeks the roadmap has published a track with no scheduled item, no end state and no
owner decision pending. That is worse than a closed track, because **an open track with nothing in
it is an invitation to drift** — and the drift has a specific destination that
[ADR-0016](0016-the-audit-is-the-product.md) already froze: engine work, dressed as usability.

## Decision

**Track B is closed. The roadmap carries Track A only.**

Reopening it takes what ADR-0009 requires of any new axis: **a defect measured in our own data**,
plus its own ADR. Not a good idea about measurement, and not an external suggestion however
credible — the same door, on the same terms, as every other axis.

## The defect it existed for is still real

Track B existed because of something measured here, and closing the track does not close the
defect. Stated plainly so that nobody has to reconstruct it later:

> **A reader who names one facet is answered 17 times out of 17. A reader who names all four is
> answered 4 times out of 192. Of the 539 nameable cells, 84.6% answer nothing at all.**

Those figures are unchanged by this decision. [ADR-0019](0019-borrowing-cannot-answer-an-unpublished-cell.md)
already recorded that declining a remedy does not shrink a defect, it only stops pretending one is
queued — and this ADR is the same sentence applied to the whole track. **The honest position is that
the corpus is most useful to a reader who describes themselves least, that this is backwards, and
that nothing is scheduled to fix it.**

What would fix it is known and unscheduled: more shards, a reader-chosen donor, or evidence
declared per cell. Each is a build, each needs its own decision, and none is owed.

## Alternatives considered

- **Leave Track B open with nothing in it.** Rejected: it is what has been happening, and it
  publishes a plan that does not exist. A reader checking the roadmap against reality finds a track
  that has not moved in five weeks and no statement of why.
- **Take the depth axis now** — evidence declared per cell, which is what would make "nearest"
  mean anything. Rejected on adoption rather than on merit: it is the largest build on the list and
  there is **no reader asking for it**. Zero audit rows, zero disputes, zero citations. Building the
  answer to a question nobody has asked is how ADR-0012's registry trial already failed once.
- **Fold the survivors into Track A.** Rejected as a rename: U1 is done and there are no survivors.

## Consequences

- **The roadmap gets shorter and truer.** One track, five milestones, and a date already committed
  in writing for the one decision that remains ([ADR-0017](0017-the-kill-criterion-gets-a-clock.md)).
- **A usability idea now needs a measured defect to enter**, which is the same bar as everything
  else and removes the standing exception a capped-but-open track created.
- **The 84.6% stays published** in the roadmap and in ADR-0019. Closing the track must not be the
  moment that figure quietly stops being mentioned; if it ever moves, it moves because someone built
  a remedy and recorded it here.
- **This narrows what RiskShard offers**, and the narrowing is the honest version of what was
  already true: the audit is the product, and the corpus answers the cells it holds.
