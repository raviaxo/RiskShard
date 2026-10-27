# The reader-chosen donor — measured 2026-10-26

*ADR-0019 declined rule-chosen borrowing and named three things that would change the defect. Two
are closed. This measures the live one, on the condition ADR-0018's amendment requires it to state
first. The condition and both thresholds were committed to `engine/donor_choice.py` before
`measure()` was run — `git log` has the two commits in that order.*

## The condition, as stated beforehand

> **If the tied donors are indistinguishable, the feature converts a rule's arbitrary tiebreak into
> the reader's arbitrary tiebreak and calls the difference agency.**

**Decline if either:** more than 50% of tied cells offer only one distinct matched-facet set, or
more than 50% have a donor value spread under 25%.

## The result

| | measured | threshold | |
| --- | --- | --- | --- |
| tied cells | **271** of 456 (59.4%) | — | matches ADR-0019 |
| only one matched-facet set among tied donors | **28.0%** (76 of 271) | decline above 50% | **clears** |
| value spread under 25% | **1.8%** (5 of 271) | decline above 50% | **clears** |
| **median spread between tied donors** | **8.83×** | — | see below |

**Verdict: proceed.** Both halves clear, and neither narrowly — 28% against a 50% bar, and 1.8%
against a 50% bar.

**What that means and only what it means.** When donors tie on how *many* facets they match, in 72%
of cases they differ in *which* facets — one matches country and threat where another matches
industry and size. A reader who knows their threat matters more than their sector has something real
to act on. The choice is not a coin flip with a label on it, which is what the condition was written
to catch.

It does **not** mean the feature is good. ADR-0018's bar is that a design state and measure its own
failure condition before it reaches a page, not that passing one makes it worth building.

## ⚠️ What the measurement surfaced that the condition did not ask about

**The median spread between tied donors is 8.83×.** When two shards are equally near a reader's
cell, the figures they would hand over differ by a median factor of nearly nine.

That clears the stated test — it is the opposite of the "choice doesn't move the answer" failure.
But it exposes a risk nobody pre-stated:

> The answer is so sensitive to the donor choice that a reader who chooses on a facet which does not
> actually drive loss receives a number wrong by close to an order of magnitude — and they will
> believe it more, not less, because they chose it.

**This is recorded as owed, not used to decline.** The thresholds were fixed before the run
precisely so the result could not be reinterpreted after seeing it, and retrofitting a third
condition now would be the move ADR-0017 stands as a warning against. The stated test passed. A new
risk appeared. It belongs to the next gate, not to this one.

**So the design owes a second measurement before any of it reaches a page:** does a reader choosing
on the facet they say matters land closer to the truth than a reader choosing at random? If the
answer is no, agency is decoration and the 8.83× is the cost of it.

That question cannot be answered from this corpus — it needs a cell where the true value is known
and 11 shards is not enough to hold one out. Which may mean this route is measurable only against
per-cell evidence, the third thing ADR-0019 named, and the heavier one.

## Status

**Not started, and not approved to start.** This is the gate ADR-0019 said the route would need, and
the route has now passed the first half of it. The next move is the owner's: accept the result and
commission the second measurement, or record the 8.83× as grounds to leave the specificity inversion
where ADR-0021 left it.

Nothing has been built. `engine/donor_choice.py` computes and reports; it has no feature in it.
