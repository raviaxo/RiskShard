# ADR-0017 — The kill criterion gets a clock, and this is the only time it moves

- **Status:** Accepted (2026-08-16)
- **Date:** 2026-08-16
- **Deciders:** repo owner
- **Amends:** [`0012-loss-event-registry-bounded-trial.md`](0012-loss-event-registry-bounded-trial.md)
  decision 5
- **Related:** [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md) (which
  disallows a second growing surface), [`0008-the-governed-tail.md`](0008-the-governed-tail.md)
  (the exceedance axis the registry was meant to serve)

## Context

[ADR-0012](0012-loss-event-registry-bounded-trial.md) adopted the loss-event registry as a bounded
trial and pre-committed its ending:

> **Kill criterion, measured at two release cycles.** […] the count of shards whose `impact.max`
> cites a registry entry rather than a one-off, and whether anyone outside the project contributes
> an entry. **If neither has moved, retire the registry rather than carry it.**

That criterion was measured at v0.9.0, the second release cycle, on 2026-08-16:

| | |
| --- | --- |
| shards whose `impact.max` cites a registry entry | **0** |
| shards that *could* cite one | **0** (1 blocked — swapping would trade an exceedance statement for provenance) |
| entries contributed from outside the project | **0** |

**Neither has moved. By its letter, the registry retires today.**

## The problem this ADR has to be honest about

**This ADR changes a kill criterion after seeing a measurement that would have fired it.** That is
the single move a pre-commitment exists to prevent, and no amount of good reasoning makes it a
neutral act. It is recorded here in those words so that nobody — including us — can later describe
it as a routine scheduling change.

The reason it is nevertheless the right call is narrow and checkable:

**v0.8.0 was cut on 2026-08-15 and v0.9.0 on 2026-08-16 — one day apart.** "Two release cycles" was
written on 2026-08-13, when this project had cut eight releases in four weeks and a cycle plausibly
meant weeks of elapsed time. It has since cut two in twenty-four hours. The criterion measures
*adoption*, and adoption cannot occur or fail to occur inside a day. **The clock ran out without
ever having started.**

Two further facts bear on it, and one cuts against the registry:

- **The outside-contributor metric is currently uninformative**, not negative. Nobody outside the
  project has contributed an entry because essentially nobody outside the project knows it exists:
  2 stars, 0 forks, no external user. That reads as "not yet asked" rather than "asked and
  refused".
- **The citation metric is getting harder, not easier, and that is our doing.** v0.9.0 retired two
  `none_known` maxima by finding an exceedance in a source we already held. Every such retirement
  *removes* a slot the registry could have filled. The registry's opportunity is shrinking as the
  audit succeeds, which is a real argument for retiring it and is recorded here rather than
  omitted.

## Decision

**The kill criterion keeps its two metrics unchanged and gains a date. It is measured at the first
release cut on or after 2026-11-01, and this is the only amendment it will receive.**

### 1. The metrics do not change

Still: shards whose `impact.max` cites a registry entry, and entries contributed from outside the
project. **If neither has moved at the measurement point, the registry retires.** ADR-0012's
reasoning for choosing those two is untouched, and lowering the bar was never on the table — the
complaint was about the clock, not the test.

### 2. The measurement point is a date, not a count of releases

**The first release cut on or after 2026-11-01.** A date because a release count is exactly what
failed here: it is under our own control, and a criterion an author can satisfy by tagging is not a
criterion. A date cannot be reached faster by working harder.

That is roughly eleven weeks from ADR-0012's acceptance, which is the shortest window in which the
audit could plausibly be published, read by someone, and acted on.

### 3. One amendment only

**This criterion does not move again.** If the measurement at that date reads zero and zero, the
registry retires, whatever is happening at the time and however promising it looks. A
pre-commitment amended twice is not a pre-commitment; it is a preference with paperwork.

### 4. The uninformative-metric case is settled in advance, not on the day

If, at the measurement point, the project still has no external readership, **the
outside-contributor metric reads zero for a reason that has nothing to do with the registry** — and
that is *not* grounds for a further extension. It is grounds for retiring the registry and
recording that the trial was never given a fair test, which is a truthful and unflattering result
this project can publish.

Deciding that now, before the day, is the point of writing it down.

## Consequences

- **The registry is carried for roughly eleven more weeks** with no expansion, exactly as
  ADR-0012 scoped it: one slice, 36 events, no exceedance claims, no non-US expansion.
- **It remains a second surface under [ADR-0016](0016-the-audit-is-the-product.md)**, which says
  the audit is the only growth surface. The registry does not grow during this period; carrying is
  not growing, and the date bounds the carry.
- **The measurement that fired is published**, so a reader can see the criterion was met and
  overridden rather than quietly reset.
- **The doctor keeps printing both counts every run**, which is what made this measurable without
  anyone remembering to look.

## Alternatives considered

- **Retire now, honouring the letter.** The cleanest option, and genuinely defensible: a retired
  experiment is a result and the registry has produced nothing in either cycle. Rejected because
  the trial was never given the elapsed time the criterion assumed, and retiring on a technicality
  produces a *result we would not believe* — the worst outcome of the three, because it looks like
  evidence and is not.
- **Keep the criterion as written and cut fewer releases.** Perverse: it makes release cadence a
  function of an unrelated experiment's clock.
- **Retire the trial but keep the 36 events** as a published dataset with no claim on the shards.
  Attractive and still available at the measurement point. Rejected *for now* only because it
  forecloses the citation metric before it has been tested; if the date arrives with both metrics
  at zero, this is the shape retirement should take rather than deleting the work.
- **Weaken the metrics instead of the clock** — e.g. counting a registry entry that *could* be
  cited. Rejected outright. That is moving the bar rather than the deadline, and it is the version
  of this amendment that would be indefensible.

## Open questions

1. **What happens to the census if the registry retires?** The EDGAR corpus census is published as
   [finding 8](../FINDINGS.md) and stands on its own regardless. Whether the 36 extracted events
   survive as a dataset is decided at retirement, not here.
