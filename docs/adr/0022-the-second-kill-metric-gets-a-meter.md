# ADR-0022 — The second kill-criterion metric gets a meter, not a new definition

- **Status:** Accepted (2026-09-28)
- **Date:** 2026-09-28
- **Deciders:** repo owner
- **Instruments:** [`0017-the-kill-criterion-gets-a-clock.md`](0017-the-kill-criterion-gets-a-clock.md),
  which set the measurement date; and through it
  [`0012-loss-event-registry-bounded-trial.md`](0012-loss-event-registry-bounded-trial.md) decision 5,
  which wrote the criterion
- **Related:** [`0004-citable-parameter-identifiers.md`](0004-citable-parameter-identifiers.md)
  (stable ids, never reused), [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md)
  (the registry does not grow during the carry)

## Context

The registry's kill criterion turns on two numbers, measured at the first release on or after
2026-11-01:

1. shards whose `impact.max` cites a registry entry
2. entries contributed from anyone outside the project

A QA pass on 2026-09-27 found that **only the first has a meter.** `engine.loss_events.trial_metrics`
generates metric 1 and a test pins it to the roadmap. Metric 2 could not be derived from the tree at
all: a loss event recorded nothing about who supplied it and the schema had no field for one, so the
function returned `None` and documented that `None` meant *unmeasured, not zero*. The roadmap and the
internal queue both published **0**.

ADR-0017 recorded 0 at v0.9.0 and already described this metric as *"currently uninformative"*, so
the published zero was not a contradiction. It was a gate nobody had built the meter for.

**Why it matters on the date and not before.** Retiring the registry on a **measured** zero and
retiring it on an **un-instrumented** one are different acts, and only the first is the criterion
working. Without a meter, the 2026-11-01 measurement would publish half a result that nothing
generated, in a project whose stated rule is that any number in public text is generated or pinned
by a test.

ADR-0017's Consequences also stated that *"the doctor keeps printing both counts every run, which is
what made this measurable without anyone remembering to look."* **It printed one.** That sentence was
untrue from the day it was written, for the same reason: there was nothing to print.

## Decision

**Metric 2 gets an instrument. The criterion itself does not move.**

### 1. Every loss-event record declares where it came from

`schemas/loss_event_schema.json` gains a required `contribution` block:

```yaml
contribution:
  origin: project | external      # required on every record
  contributor: <handle or name>   # required when origin is external
  contributed_date: <ISO date>    # required when origin is external
```

**Required, not optional.** An optional field reproduces the defect it is meant to fix: a missing
value and a declared zero would again be indistinguishable. All 36 existing records declare
`origin: project`, which is true of every one of them — they were extracted by the project from
EDGAR.

`contributor` and `contributed_date` are required when `origin` is `external` so that the count is
**attributable rather than self-asserted**, and so a contribution arriving after the measurement
date can be told from one that arrived before it. Credit is by handle, as published, consistent with
how every other outside contribution to this project is credited.

### 2. An outside contribution arrives as its own file

`loss_events/sec_filings_2023_2026.yaml` is generated from an internal extraction table and its
header forbids hand-editing, so an external record cannot be added to it without breaking the
guarantee that a record and its verification never drift apart.

The loader already reads every `loss_events/*.yaml`. **An outside contribution therefore lands as a
new file in that directory** and never touches the generated one. This is recorded because it was
not obvious: instrumenting the metric surfaced that the contribution route was not merely
undocumented, it was structurally closed.

### 3. `trial_metrics` counts, and the doctor prints both

`external_contributions` becomes a count of records declaring `origin: external`, with
`external_contribution_ids` alongside it so the number can be checked rather than believed. The
doctor's loss-event line now prints both kill-criterion counts, which makes ADR-0017's claim about
itself true.

### 4. This is not a second amendment to the criterion

ADR-0017 section 3 says the criterion does not move again. **Nothing here moves it.** The two
metrics are the ones ADR-0012 wrote, the threshold is unchanged, the date is unchanged, and the bar
is not lowered. Instrumenting a test is not weakening it, and this ADR would be indefensible if it
did either.

## Consequences

- **Metric 2 reads 0 on 2026-09-28, measured.** The number does not change; what changes is that it
  is now generated from the tree rather than asserted in prose, and a reader can see what it counted.
- **The zero is still not evidence that anyone declined.** It counts accepted records, so it reads
  zero while nobody has contributed one *and* while nobody has been asked to — the same number and a
  different fact. **ADR-0017 section 4 settled that case in advance:** no external readership at the
  date is grounds for retiring the registry, not for extending it again. The meter exists to make
  the zero honest, not to rescue it, and this consequence is written here so that nobody reads the
  new instrument as a reason to relitigate the date.
- **A schema change invalidates any record written against the old schema.** There are none outside
  this repository, the registry has never been published as a contributable artifact, and the gate
  fails loudly rather than silently if one appears.
- **The registry still does not grow.** ADR-0016 allows one growth surface and it is the audit.
  Adding a provenance field is not an expansion; it does not admit a single new event.

## Alternatives considered

- **State in ADR-0017 that the criterion turns on metric 1 alone**, recording the absence of a
  contribution route as the reason metric 2 was never measurable. Genuinely defensible, cheaper, and
  it needed no schema change. **Rejected by the owner on 2026-09-28** in favour of instrumenting:
  dropping a metric after seeing that it cannot be measured is the same class of move as amending a
  criterion after seeing a measurement, and ADR-0017 already spent this project's one allowance for
  that.
- **Make the field optional.** Rejected: it reproduces the exact ambiguity — absent versus zero —
  that the ADR exists to remove.
- **Infer origin from the file a record sits in.** Rejected: it makes a governance fact a
  side effect of file layout, and a record moved between files would silently change the metric.
- **Record contributions in a separate ledger outside the registry.** Rejected as a second surface
  that would drift from the records it describes; the provenance of a record belongs on the record.

## Open questions

1. ~~**Should a contribution route be documented and offered before 2026-11-01?**~~ **Answered
   no, 2026-09-29.** The meter can only ever read what a route delivers, and there is no
   loss-event-specific route today. This ADR did not decide whether to build one — it made the
   absence visible, which is what a meter is for.

   **The reason is a measurement, not the calendar.** "Too late" would have been the weak
   argument and it invites reopening. `citation_candidates()` was run across all 11 shards on
   2026-09-29 and the blockage is **population, not volume**:

   - **10 of 11 shards have no country-and-threat match at all.** The corpus is US/GB/IE SEC
     filings; the grid is AU · CA · DE · FR · GB · JP · SG · US midmarket. It holds **no
     business-email-compromise events**, so the three BEC shards cannot match a corpus of this
     shape however many records it gains.
   - **1 of 11 matches and is correctly blocked.** `us_finance_data_breach_midmarket` matches
     four events, two on industry as well, but its `impact.max` carries `observed_rank` — one of
     only two informative exceedance statements in the portfolio — and a registry entry carries
     none by rule. Citing one would trade an exceedance statement for provenance, a regression
     under [ADR-0008](0008-the-governed-tail.md).

   So a contributed record would be one more event of the same shape against the same mismatch.
   **The only route that would help is one soliciting the missing slice** — non-US, and BEC — and
   `loss_events/README.md` states that expansion beyond this slice is *"not authorized"* by
   [ADR-0012](0012-loss-event-registry-bounded-trial.md). Offering that route would amend the
   trial by the back door, 33 days before its kill date, which is exactly the sunk-cost move
   [ADR-0017](0017-the-kill-criterion-gets-a-clock.md) exists to refuse and the reason roadmap
   M3b is deliberately not started.

   **What this obliges at the measurement, recorded now rather than discovered on the day.**
   The criterion will retire the registry, and read literally it reports *nobody cited and nobody
   contributed*. Both zeros are true and neither is about adoption. The honest statement, which
   M4 is to publish in these terms: **the registry was built on a corpus that structurally cannot
   serve the grid it was meant to serve, and was forbidden from growing into a shape that
   could.** `loss_events/README.md` has said since the first reading that zero citations here
   means *nothing fits yet*, not *nobody bothered* — that distinction survives to the
   measurement, and it argues for retirement rather than against it, because a registry that
   cannot serve the shards is not waiting on readers. Writing this before 2026-11-01 makes it a
   pre-commitment; writing it after would make it a rationalisation.
