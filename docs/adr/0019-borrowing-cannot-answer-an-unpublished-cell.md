# ADR-0019 — Nearest-shard borrowing cannot answer an unpublished cell, and is declined

- **Status:** **Proposed (2026-08-23)** — recommends **declining** roadmap U2 / execution-plan W4.
  Closing a roadmap axis is the owner's call; the measurement below is not.
- **Date:** 2026-08-23
- **Deciders:** repo owner
- **Related:** [`0018-the-target-selector-failed-measurement.md`](0018-the-target-selector-failed-measurement.md)
  (whose amendment required this failure condition to be stated *before* building),
  [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md) (the scope gate this
  would have needed an amendment to pass), [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md)
  (quantification is the reader's step), [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md)
  part 2 (the shard count is frozen), [`0007-construct-coherence.md`](0007-construct-coherence.md)
  (borrowing-only restriction)

## Context

`engine/cell_coverage.py` measures a defect that is real and is ours: **the corpus answers a reader
who tells it nothing and refuses one who describes themselves.** A reader naming one facet is
answered 17 of 17 times; one naming all four is answered **4 of 192**.

The proposed remedy was nearest-shard borrowing — for a cell with no anchors, take the nearest
published shard's anchor set whole and label what was borrowed. It is cheap to build, it needs no
backend, and the composition disclosure shipped in v0.11.0 would make the borrowing visible rather
than silent.

[ADR-0018](0018-the-target-selector-failed-measurement.md)'s amendment set one condition on it: a
design whose output is never empty owes **its own failure condition, stated before it ships**,
because ADR-0014 shipped a control decided on what the page could cheaply compute and never on what
its answers would say.

## The failure condition, and it fired

Stated as: *does a reader who names an unanswerable cell receive an answer that is about their
cell?* Measured by `engine/borrowing.py`, which builds no feature:

| | |
| --- | ---: |
| cells the corpus cannot answer | **456** |
| distinct answers borrowing could return | **11** |
| cells with no single nearest shard | **271 (59%)** |
| same, sector-weighted | 276 (61%) |

**456 dead ends would become 456 relabelled copies of 11 numbers.**

**The ceiling is structural, not a tuning problem.** A borrowed answer *is* some shard's answer, so
distinct answers can never exceed the shard count under any donor rule — and ADR-0016 part 2 freezes
the shard count, so it cannot be raised by adding cells either.

**The tie rate is the sharper finding.** For a clear majority of cells, several shards are equally
near and "nearest" does not pick one. The figure a reader receives is then decided by a tiebreak
carrying no evidentiary meaning: ordering by id sends most of them to whichever shard sorts first,
which is why 252 of 456 land on Australian shards. **Sector-weighting, the obvious fix and the
intake scorer's own ranking, makes it worse.**

## Decision

**Decline nearest-shard borrowing as the mechanism for arbitrary cells.** Roadmap U2 and
execution-plan W4 close.

## Reasoning

**It automates a judgment the data cannot support, and dresses it as a computed answer.** A
practitioner outside our eleven cells can already read the eleven items and decide for themselves
which is nearest — that is a judgment with their context in it. Borrowing makes that choice for
them, arbitrarily in the majority of cases, and returns it with the authority of something
calculated. That is [ADR-0010](0010-where-riskshard-stops.md)'s line, and it is
[finding 2](../FINDINGS.md)'s shape: a number assembled to look like a reading of one thing.

**The label does not save it.** The composition disclosure is honest and it works. But "100%
borrowed on industry and threat" attached to a figure chosen by alphabetical tiebreak describes the
borrowing accurately and the *choice* not at all. The reader cannot tell that four other shards were
equally near.

## What is explicitly not the reason

- **Not that it is hard.** It is roughly fifty lines on top of `engine/composition.py`.
- **Not that the disclosure would be dishonest.** v0.11.0 shipped exactly the machinery to state it.
- **Not that ADR-0009 forbids it.** The specificity inversion is a defect measured in our own data,
  which is the one door ADR-0009 leaves open. The amendment was available. **It is declined on what
  the answers would say, not on whether it was permitted** — which is the distinction ADR-0014
  failed to draw.

## What would change this

1. **Many more shards**, so that "nearest" is usually unambiguous. Closed while ADR-0016 part 2
   stands, and that ADR is the reason the shard count is frozen at all.
2. **The reader picks the donor**, rather than a rule picking it for them. That is a different
   feature with a different failure mode, and it would need its own measurement — note it revives
   the control ADR-0018 retired, so it inherits those preconditions.
3. **Evidence declared per cell rather than per shard**, which would make nearness a property of the
   data instead of an artefact of how we packaged it. That is the depth axis ADR-0006 describes.

## Consequences

- **The specificity inversion remains a measured defect with no accepted remedy.** Recorded plainly
  rather than left on a roadmap implying work is queued against it.
- **`engine/borrowing.py` stays**, with its tests, as the record of why. If the corpus changes
  enough to move these numbers, the tests fail and this ADR is owed a re-read.
- **The process paid for itself.** ADR-0018's amendment required the failure condition first; stating
  it killed the feature before a line of it was written. That is the opposite of ADR-0014, where the
  same question was asked four days after shipping.
