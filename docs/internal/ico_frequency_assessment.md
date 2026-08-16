# The ICO breach dataset cannot supply a GB frequency parameter

*Tested 2026-08-16. Declined. This note exists so nobody spends the work again without
first reading why it does not close.*

## What was proposed

The GB financial-services data-breach shard takes all three frequency anchors from the UK
DSIT Cyber Security Breaches Survey, and all three are **bridged on sector** — DSIT is an
all-industry survey, and the shard is financial services.

The ICO publishes quarterly personal-data-breach case data with a `Sector` field. Eight
quarters are held locally: **24,154 cases, 5,694 flagged as cyber incidents, of which 1,970
are Finance/insurance/credit and 707 of those are cyber.** That looked like the obvious fix
— a sector-specific, country-specific numerator to retire a sector bridge.

## Why it does not close

**The two sources measure different things, and the gap is two orders of magnitude.**

- **DSIT** asks organizations whether they *identified a breach or attack* in the last 12
  months. It is a **survey prevalence**: 43% of all businesses, 65% of medium businesses.
- **The ICO** counts *personal-data breaches notified to the regulator*. It is a **reported
  incidence** over the whole population of UK organizations.

Finance-sector cyber cases reported to the ICO run **357 in FY2024/25 and 337 in FY2025/26**.
Turning that into a rate needs a denominator, and no denominator makes it comparable:

| assumed UK finance firms | implied annual rate |
| ---: | ---: |
| 10,000 *(implausibly low)* | 3.57% |
| 30,000 | 1.19% |
| 60,000 | 0.59% |
| 90,000 | 0.40% |

**The existing sourced floor is 43%.** Even at a denominator small enough to be indefensible,
the ICO-derived rate is an order of magnitude below it; at a realistic one it is roughly
**73× lower**.

That is not a disagreement between two estimates of the same quantity. It is the signature of
two different quantities: almost every organization that identifies an attack does **not**
notify the ICO, because most identified attacks are not reportable personal-data breaches.

## The precedent this matches exactly

The Japan shard faced the same shape and reached the same answer. From `NEXT_STEPS.md`:

> finish honestly with **survey-prevalence** for `frequency.likely/max` … **not** the NPA÷census
> ratio, which is a reported-incidence floor (~0.0002, below the existing sourced min).

The NPA ratio was rejected for being a reported-incidence floor beneath the sourced minimum.
The ICO ratio is the same instrument in a different jurisdiction, and it fails the same test.

## What would have happened if we had shipped it

`frequency.min` would have dropped from **0.43 to roughly 0.006**, the simulated loss would
have fallen through the floor, and the change would have been recorded as an *improvement*
because the new anchor is sector-specific and country-specific and regulator-sourced. Every
one of those adjectives is true. The number would still have been wrong, because the
construct changed underneath it.

**This is [finding 2](../FINDINGS.md)'s problem arriving as an upgrade.** A sector bridge is a
real defect; swapping the measured quantity to close it is a worse one.

## What the ICO data *is* good for

Recorded so the effort is not wasted:

- **A population source.** It is already audited as one — the strongest population statement
  in the corpus, being a mandatory-notification frame rather than a survey sample.
- **Sector composition.** 707 of 5,694 cyber cases are finance — a defensible statement about
  the *share* of reported cyber breaches arising in the sector, which is a different claim
  from a rate and does not need a denominator.
- **A floor on reporting, if ever wanted explicitly.** Declared as a reporting rate rather than
  a prevalence, it would be honest. Nothing in the model currently wants that quantity.

## What would actually retire the GB sector bridge

A **financial-services-specific breach or attack prevalence for the UK**, measured the way DSIT
measures — an organizational survey, not a regulator's case count. DSIT publishes sector
breakdowns in some cycles; that is the thing to look for, and it is a reading task rather than
a derivation task.
