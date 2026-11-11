# ADR-0025 — The registry trial is retired on its own criterion, and the 36 events survive it

- **Status:** Accepted (2026-11-11)
- **Date:** 2026-11-11
- **Deciders:** repo owner
- **Executes:** [`0017-the-kill-criterion-gets-a-clock.md`](0017-the-kill-criterion-gets-a-clock.md)
  §2 (the measurement date) and §4 (the uninformative-metric case)
- **Retires:** the bounded trial adopted by [`0012-loss-event-registry-bounded-trial.md`](0012-loss-event-registry-bounded-trial.md),
  and with it [`0005-documented-loss-event-registry.md`](0005-documented-loss-event-registry.md)
  as a live proposal
- **Related:** [`0022-the-second-kill-metric-gets-a-meter.md`](0022-the-second-kill-metric-gets-a-meter.md)
  (built the meter that makes metric 2 a measurement rather than an assertion),
  [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md) (why a second growing
  surface was disallowed), [`0008-the-governed-tail.md`](0008-the-governed-tail.md) (the exceedance
  axis the registry was meant to serve)

> **A note on the number.** [`docs/internal/m4_runbook.md`](../internal/m4_runbook.md), written
> 2026-10-26, calls this ADR "ADR-0024". That number was taken on 2026-11-11 by
> [ADR-0024](0024-the-published-bracket.md), a few hours before this was written. The runbook is
> left as it was rather than edited, because it is the record of what was decided in advance.

## The measurement

Taken **2026-11-11**, before anything was cut, by the tool that owns it — `trial_metrics()` in
`engine/loss_events.py`, built for this purpose by [ADR-0022](0022-the-second-kill-metric-gets-a-meter.md).
Output recorded verbatim:

```json
{
  "registry_events": 36,
  "shards_citing_a_registry_entry": 0,
  "citing_shards": [],
  "external_contributions": 0,
  "external_contribution_ids": []
}
```

| ADR-0012 decision 5 metric | threshold | measured 2026-11-11 |
| --- | --- | --- |
| shards whose `impact.max` cites a registry entry | any movement off zero | **0** |
| entries contributed from outside the project | any movement off zero | **0** |

The doctor's loss-event line, same day: *"36 events, 48 typed amounts (12 are
recoveries/settlements/deltas, not event costs); trial: 0 of 11 shards cite an entry, **0 could**
(1 blocked: swapping would lose an exceedance statement); 0 entries contributed from outside the
project."*

**Neither metric moved. [ADR-0017](0017-the-kill-criterion-gets-a-clock.md) §4 pre-decided what
that means: retire the registry, and record that the trial was never given a fair test.**

## The criterion fired exactly as written, ten days later than the queue expected

ADR-0017 §2 set the measurement at **the first release cut on or after 2026-11-01**, and chose a
date over a release count precisely because a release count *"is under our own control, and a
criterion an author can satisfy by tagging is not a criterion."*

This is that release. It is cut on 2026-11-11, which is on or after 2026-11-01, so **the condition
is satisfied literally and the date did not move.** What slipped is not the criterion but the
queue: `docs/internal/NEXT_STEPS.md` carried *"the 2026-11-01 measurement is 10 days away"* for ten
days past the trigger, and no session opened in between.

Worth separating the two, because they are different failures with different costs. A date that
moves destroys a pre-commitment. A date that passes unnoticed costs ten days of a stale queue —
and, if the measurement had been capable of changing in that window, it would also have cost the
right to call the result clean. It was not capable of changing: no shard can begin citing an entry
without a parameter change, and no contribution route exists to deliver an outside entry. **The
numbers on 2026-11-11 are the numbers that would have been read on 2026-11-01.** Recorded rather
than smoothed over.

## Decision

### 1. The trial is retired

The bounded trial of ADR-0012 ends here, on the criterion it pre-committed to, at the date
ADR-0017 fixed. ADR-0005 stops being a live proposal. Reopening either takes a new ADR and a
measured defect, not a change of mind.

### 2. The 36 events are kept as a published dataset with no claim on the shards

[ADR-0017](0017-the-kill-criterion-gets-a-clock.md)'s Alternatives pre-specified the shape in these
words: *"Retire the trial but keep the 36 events as a published dataset with no claim on the
shards… if the date arrives with both metrics at zero, this is the shape retirement should take
rather than deleting the work."*

So nothing is deleted. `loss_events/` keeps its records, its schema and its 16 tests. What it loses
is standing: **no shard parameter may cite a registry entry, and the registry makes no claim to
calibrate anything.** It is a documented dataset of 36 events with 48 typed amounts, of which 12
are not event costs, and that typing remains its most useful property.

This also answers ADR-0017 open question 1 with the same sentence that pre-specified it: the 36
events survive, and the EDGAR census stands on its own as [Finding 8](../FINDINGS.md) regardless.

### 3. The honest statement of why both metrics read zero

Carried across verbatim from [ADR-0022](0022-the-second-kill-metric-gets-a-meter.md)'s
open-question closure, written before the measurement so that it is a pre-commitment and not a
rationalisation:

> **The registry was built on a corpus that structurally cannot serve the grid it was meant to
> serve, and was forbidden from growing into a shape that could.**

Read literally the criterion reports *nobody cited and nobody contributed*. Both zeros are true and
**neither is about adoption**:

- **Metric 1 is population mismatch, not neglect.** `citation_candidates()` reports 0 of 11 shards
  cite an entry and **0 could**. Ten have no country-and-threat match — the corpus is US/GB/IE, the
  shards are AU·CA·DE·FR·GB·JP·SG·US, and there are no BEC events in it at all. The eleventh,
  `us_finance_data_breach_midmarket`, is blocked for a reason that is a feature: its maximum carries
  `observed_rank`, a registry entry carries no exceedance by rule, so citing would trade an
  exceedance statement for provenance — a regression under [ADR-0008](0008-the-governed-tail.md).
- **Metric 2 is a route that was never offered, deliberately.** ADR-0022 open question 1 closed on
  2026-10-22: the only route that would have moved it solicits the slice ADR-0012 forbids. The
  meter reads a measured zero that means *never asked*.

`loss_events/README.md` has said since the first reading that zero citations means *nothing fits
yet*, not *nobody bothered*. That distinction survives the measurement, and it **argues for
retirement rather than against it** — a registry that cannot serve the shards is not waiting on
readers.

### 4. The instruments stay, as the record of the result

- `engine/loss_events.py` keeps `trial_metrics()`. It is no longer a live criterion; it is the
  record of how the trial ended, and it must keep returning the numbers above.
- The doctor's loss-event check becomes a **retirement record** rather than a live criterion. It
  keeps printing both counts, because a retired trial whose numbers stop being visible is
  indistinguishable from one that was quietly dropped.
- `schemas/loss_event_schema.json` keeps the `contribution` block. It is **vestigial**, and saying
  so costs less than a migration — ADR-0022 built it five weeks before the thing it metered was
  retired, which is the correct order and still a cost worth naming.

## Consequences

**The project now has a pre-commitment it kept.** A criterion was written with a threshold and a
date, the date was not moved when the result became predictable, one amendment was allowed and
spent on an instrument rather than an escape, and the trial was retired on an unflattering reading
rather than extended on a hopeful one. That is the consequence that matters, and it is worth more
than the registry was.

**M4 closes with this ADR.** M5 is measured at the same moment and is **not** closed by it — a
claim an earlier draft of this ADR made and which is wrong. M5 is the adoption test (has anyone
cited a parameter or the audit, disputed a row, or applied the standard to a source we did not
read?), and none of its three questions depends on the registry. Measured the same day:
**all three still read zero** — 4 stars, 0 forks, 0 external pull requests, 0 issues or discussions
from anyone but the owner. M5 stays open with its date refreshed, because it measures something
this repository cannot generate and retiring it would be retiring the only honest adoption
reading the project has.

**ADR-0022's meter was built for a measurement that retired the thing it measured**, and that is
not waste: before it, `trial_metrics` returned `None` for metric 2 while the roadmap and the queue
published **0**. The result did not change. What changed is that the zero above is measured, and a
retirement on an asserted number would have been a weaker claim than this one.

**What this does not touch.** No parameter value moves; this is a governance release.
[Finding 8](../FINDINGS.md) (the EDGAR census) stands. The 36 events remain citable, and
`tests/test_release_archives.py` plus the pinned-citation guarantee in `docs/CITING.md` still
apply to them.

## Alternatives considered

**Extend the trial because the project has no readership yet.** Refused in advance by ADR-0017 §4,
in writing, for exactly this situation. Taking it now would be the second amendment to a criterion
that allowed one, which ADR-0017 §3 calls *"a preference with paperwork."*

**Delete the registry.** Refused by ADR-0017's Alternatives. The 36 events cost real work, the
typing of the 48 amounts is a genuine contribution, and citations may already pin them. Retirement
is a loss of standing, not of data.

**Narrow the criterion to metric 1 alone.** This was a live option on 2026-09-28 and the owner
chose to instrument metric 2 instead ([ADR-0022](0022-the-second-kill-metric-gets-a-meter.md)).
Revisiting it now, after the measurement, would be choosing the criterion to fit the result.

## Open questions

1. **Does anything replace the exceedance denominator the registry was meant to supply?**
   Partly answered already, and not by the registry: [ADR-0024](0024-the-published-bracket.md)
   found a published distribution with revenue-banded percentiles inside a source the corpus
   already held, and placed all 11 published maxima against it. That is a weaker instrument than a
   per-event registry would have been and a stronger one than the registry ever became. Whether
   the gap that remains is worth a new objective is **not decided here.**

2. **Does the retired dataset keep earning its tests?** 16 tests and a doctor check now guard a
   dataset with no claim on anything. They stay for this release because deleting coverage in the
   same change that retires a surface makes both harder to audit. Whether they shrink later is
   open.
