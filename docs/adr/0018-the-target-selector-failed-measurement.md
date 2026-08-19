# ADR-0018 — The reader-supplied target selector failed measurement, and is retired

- **Status:** Accepted (2026-08-19)
- **Date:** 2026-08-19
- **Deciders:** repo owner
- **Supersedes:** [ADR-0014](0014-the-reader-supplies-the-target.md) parts 1, 4 and 5 (the UI
  control and its counts). ADR-0014's *principle* — fit is meaningless without a stated target —
  survives intact and is unchanged.
- **Related:** [`0011-fit-is-a-facet-set.md`](0011-fit-is-a-facet-set.md) (no composite score,
  ever — still binding), [`0013-fit-is-derived-not-stored.md`](0013-fit-is-derived-not-stored.md)
  (fit is derived; unchanged), [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md)
  (what the front door is for)

## Context

[ADR-0014](0014-the-reader-supplies-the-target.md) shipped a control on the explorer letting a
reader name their own cell — country, sector, size, threat — and recomputed every fit line against
it in the browser. The reasoning was sound: fit against *our* cell is a convenience for one reader,
and the page already carried `declared_for` on every parameter, so answering the reader's own
question cost almost nothing.

**It was never measured against the corpus it had to answer over.** On 2026-08-19 it was, by
replaying the engine's own fit rule across every target the control offers:

| | |
| --- | ---: |
| selectable non-empty combinations | **539** |
| combinations answering **nothing** | **456 (84.6%)** |
| combinations answering at least one parameter | **83** |
| **trap pairs** — two values that each answer alone and nothing together | **60** |

A trap pair is the shape a reader meets one dropdown at a time. `AU` answers 14 parameters and
`manufacturing` answers 4; `AU + manufacturing` answers nothing. The owner hit that exact pair on
the second thing he tried and read the page as broken rather than as honest.

**The first attempt at this measurement was wrong, and the correction is recorded rather than
quietly applied.** An ad-hoc script read the size facet under the key `sizes` where the payload
says `company_size_bands`, so size was never tested: the grid came out 215 combinations with 138
empty (64%) instead of 539 with 456 empty (84.6%), and the claim *"every combination containing
`manufacturing` returns 0"* was false — `manufacturing` answers 4 on its own. **The decision
survived the correction and the case for it got stronger.** The numbers did not survive, which is
why they now live in [`engine/cell_coverage.py`](../../engine/cell_coverage.py) with
`tests/test_cell_coverage.py` checking this document against them on every run.

## Decision

**1. The target selector is removed from the explorer.** Fit is again computed against each item's
own cell, and the fit line continues to name the cell it was computed against, so a screenshot
cannot lose the target ([ADR-0011](0011-fit-is-a-facet-set.md) is unaffected).

**2. `declared_for` stays on every parameter and stays rendered.** It is the population the source
measured — a property of the record, true for every reader, and the thing that made the derivation
possible in the first place. Nothing about the data changes; this retires a control, not a field.

**3. Restricting the dropdowns to combinations that answer something is refused.** That removes
the dead ends by hiding the coverage gap, which is the opposite of what this project is for. A
reader is entitled to find out that the corpus has nothing for Germany.

**4. The coverage gap is published instead of being made interactive.** What the selector was
groping at is a real question — *is there evidence for my cell?* — and it deserves a plain answer
rather than a control that answers it 138 different ways. The honest form of that answer is the
audit and the request route, both already on the page.

**5. This is recorded as a feature that was measured and failed, not as a redesign.** ADR-0014 was
decided on reasoning about what the page could cheaply compute, and never on what the answers would
say. That is the defect. **A feature whose most common output is "nothing here" is a feature that
teaches readers to leave**, and no amount of correctness in its computation changes that.

## Consequences

- The explorer loses its only interactive control. It is a document again, which is what
  [ADR-0016](0016-the-audit-is-the-product.md) says the front door is.
- **No published figure moves.** The released cell-matched (7) and bridged (59) counts describe our
  cell and always did; they are unchanged.
- ADR-0011's open question 1 — *should a consumer-supplied target become a first-class artefact?* —
  reopens, now with a measurement attached to it. **Two conditions must both hold before it is
  attempted again**, and both are false today:

  1. **No trap pairs.** No two facet values may each answer alone and answer nothing together.
     There are 60 such pairs today.
  2. **A majority of selectable combinations answer at least one parameter.** 83 of 539 do
     today, which is 15%.

  These are coverage preconditions, not design ones. **The control was never the problem; the
  corpus behind it was**, and rebuilding the control without moving those two numbers would
  reproduce this ADR exactly.
- The removal is part of a wider front-door density cut on the same date: the page carried 1,676
  words of prose before the first item rendered, and now carries 706. The basis of preparation moved
  to [`docs/BASIS_OF_PREPARATION.md`](../BASIS_OF_PREPARATION.md).
