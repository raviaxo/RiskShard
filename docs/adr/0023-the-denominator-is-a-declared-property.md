# ADR-0023 — The denominator becomes a declared property of an audited source

- **Status:** Accepted (2026-10-24); **scope narrowed 2026-10-26 by the first batch's own
  measurement** — the corpus-wide re-read is dropped and the property is kept for the sources
  where the base is genuinely unclear (see *Amendment*)
- **Date:** 2026-10-24
- **Deciders:** repo owner
- **Instruments:** [`0016-the-audit-is-the-product.md`](0016-the-audit-is-the-product.md) part 1,
  which names the audit as the only growth surface and sets the test every new objective must
  pass; and [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md), which
  allows a new declared axis **only** when it is born from a defect measured in our own data
- **Related:** [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md) (`population_match`
  — *who was measured*), [`0007-construct-coherence.md`](0007-construct-coherence.md)
  (`measurement_basis` — *what quantity was measured*),
  [`0008-the-governed-tail.md`](0008-the-governed-tail.md) (`exceedance_basis` — *what is known
  about being exceeded*), [`0018-the-target-selector-failed-measurement.md`](0018-the-target-selector-failed-measurement.md)
  (a new reader-facing thing owes its failure condition **before** it ships)

## Context

The audit asks four questions of every registered source. Does it publish a mode, a distribution,
an exceedance statement, and who was measured. None of them asks what a published percentage is a
percentage **of**.

That is the error this corpus most often catches other people making, and it is recorded nowhere.

**The defect, measured rather than asserted.** `engine/denominator.py` generates it, so the premise
of this ADR can be re-run rather than believed:

| | of 65 read sources |
| --- | --- |
| **declare** a denominator | **0** |
| mention one **incidentally**, inside an answer to a different question | 36 |
| **silent** — no denominator appears at all | 29 |

Zero is not an oversight. There is no field, so there is nothing to fill in. Where a denominator
survives at all it survives by accident, in prose written to answer something else — which means it
is reachable only by a reader who already knows to look for it, and that is not the reader this
corpus is for.

**Why `population` does not already answer this.** ADR-0003's `population_match` asks *who was
measured*, and a report can describe its sample frame precisely and still print a percentage over a
sub-population of it. The NPA workbook is the clean demonstration — the population is stated in
unusual detail (226 reports, split by size and industry), and the cost table is n=89 while the
recovery-duration table is n=107, both subsets. A perfect `population` answer and three different
denominators in the same document.

**What it costs a reader to not have this.** *"10 to 50 million yen is the most common cyber cost in
Japan"* is 32 of 89 cases, and it is investigation cost rather than total event loss. Both
qualifications are printed in the workbook. Neither is in the sentence that gets quoted. A reader
who carries that figure into a board paper has overstated how common the band is and has described
a forensics invoice as the loss.

## Decision

**The denominator becomes a fifth declared property on the audit record, read from the artifact like
the other four. It is read, never parsed out of existing prose.**

### 1. The property

```yaml
denominator:
  basis: verified_against_artifact            # how we know — the existing enum
  publishes: <bool>                           # does the source publish any percentage
  base: stated | derivable | ambiguous | not_applicable   # what the answer is
  verified_on: <ISO date>
  detail: <what the base is, in the report's own words where it names one>
```

**`base` is a new field name and that is deliberate.** An earlier draft of this ADR put the four
values on `basis`, which already exists on all four questions and already means something else —
*how the answer was verified* (`verified_against_artifact`, `derived_from_corpus`, `unverified`,
`no_readable_artifact`). Overloading it would have made the fifth property the only one where
`basis` meant a different thing, which is the kind of quiet inconsistency that costs a reader an
hour. Caught by reading `schemas/source_audit_schema.json` before writing the field rather than
after.

- **`stated`** — the report names the base of its own percentage.
- **`derivable`** — the base is not stated but is recoverable from figures the report prints.
  Recovering it is the reader's work, not the publisher's, and that distinction is the same one
  ADR-0008 draws between deriving and stating.
- **`ambiguous`** — the report prints a percentage and never fixes its base. The most misquotable
  shape there is.
- **`not_applicable`** — the source publishes no percentage, so there is no base to name. Expected
  to be common and honest; official statistical tables and legal instruments will sit here.

### 2. It is read, not scraped

The 36 incidental records are **a work estimate and nothing else.** Parsing a denominator out of
prose and writing it into a field would manufacture exactly the false precision this audit exists to
catch, and it would break the guarantee that every audit answer was verified against the stored
artifact. An incidental mention means a transcriber has something to work from. It never means the
corpus holds the value.

### 3. The failure condition, stated before any reading starts

ADR-0018's amendment requires this and it is not optional. The analogue of *"a feature whose most
common output is 'nothing here' teaches readers to leave"* is:

> **A column that says the same thing most of the time is ceremony, not information.**

So: **read the first 15 sources, then stop and look.** If any single basis holds more than 85% of
those 15, the property does not discriminate between sources and this ADR is retired rather than
completed — the remaining 50 re-reads are not spent. Recorded now, with the number fixed now, so
that it cannot be adjusted once the first batch is in.

The plausible way this fails is `stated` running away with it. If publishers almost always name
their base, then the denominator was never the corpus's problem and the honest finding is that the
gap is entirely on the reader's side — which is worth publishing and is **not** worth a fifth
column.

### 4. This does not reopen the audit's scope

The audit is a finite table of registered sources and this adds a column to it, not a row to
something infinite. ADR-0016 part 1's test — *does this add a row to a finite table, or a parameter
to an infinite one?* — is passed. No new source is registered by this ADR, the shard freeze is
untouched, and the engine is untouched.

## Consequences

- **Every existing audit record becomes incomplete on the day this is accepted**, and the gate
  should say so rather than treating an unread denominator as an absent one. The same distinction
  ADR-0022 drew between *unmeasured* and *zero*.
- **65 re-reads are owed**, against artifacts already stored and hashed, so no source needs
  re-obtaining. The 10 unobtainable sources stay unobtainable and are out of scope here.
- **The work is publishable throughout.** Each batch can surface a finding, which is how the first
  four questions were done and why the audit took the shape it did.
- **A fifth question changes what the read-a-source ask costs** (ADR-0016 part 4 sized it at twenty
  minutes). Whether an outside contributor is asked four questions or five is left to the
  implementation, because nobody has yet completed the four-question version.

## Alternatives considered

- **Extract the denominator from the existing prose.** Cheapest by a wide margin and rejected
  outright. 36 of 65 records would yield something, 29 would not, and every value would be a
  regex's reading of a sentence written for another purpose. It would put unverified numbers behind
  a surface whose entire claim is that every answer was checked against the publisher's own file.
- **Record it inside `population` rather than as its own property.** Rejected: the NPA record shows
  one population carrying three denominators, so folding them makes the common case unrepresentable
  and the field would have to be prose again.
- **Publish the denominator index as a one-off page without a schema change.** Attractive, and it
  is what was proposed on 2026-10-22 before the coverage was measured. Rejected once the
  measurement came back — a page built from 13 strong records and padded to 36 is the kind of
  artifact this project exists not to produce.
- **Do nothing and write the finding instead.** Genuinely defensible. The finding — *publishers
  mostly state their base, readers drop it* — is true, publishable, and costs nothing. It is
  **not** rejected; it is the thing to publish first, and section 3's failure condition is the
  circumstance in which it becomes the whole of the result.

## Amendment — 2026-10-26: the measurement that cleared this also shrank it

The stop-and-look ran as section 3 specified. **`stated` held 12 of 15, which is 80.0%**, under the
85% threshold fixed in advance, so this ADR survived its own test — by three points.
[`../internal/denominator_first_batch.md`](../internal/denominator_first_batch.md) holds the batch,
the evidence and the per-source reasoning.

Clearing the bar is not the same as being worth the full programme, and the result says so. A
column that reads `stated` four times in five is close to the ceremony section 3 exists to catch.
The value of the property is concentrated in the sources where the base is **not** clear, and
reading fifty clean reports carefully in order to write `stated` fifty more times buys almost none
of it.

### 1. The corpus-wide re-read is dropped

**Sections 1 and 2 stand. The 65-source re-read in Consequences does not.** The field is kept, the
vocabulary is unchanged, and nothing about how a value is obtained is relaxed — a recorded
denominator is still read from the artifact and still never parsed out of prose.

What changes is which sources get read. A source is read for its denominator when there is reason
to think its base is unclear, not because it is next in a queue. Finding those is a screening
problem, and screening is cheap in a way that reading is not.

**This is a narrowing, not a weakening, and the difference matters.** The bar for recording a value
is identical. Fewer sources are nominated for the work.

### 2. `base` means *named*, not *named and countable*

Open question settled, and settled on the definition rather than on the count — the batch showed
that `bci_supply_chain_resilience_2024` turns on it and would move the headline figure from 12 of
15 to 11 of 15, which is exactly the circumstance in which a definition must not be chosen by its
effect ([ADR-0017](0017-the-kill-criterion-gets-a-clock.md) is the standing warning).

The argument is separation of concerns, and it is the same one that made `base` a separate field
from `basis` in the first place. **`base` asks what the percentage is over. `population`
(ADR-0003) already asks how many were measured and who they were.** BCI saying *"17.1% of
respondents"* without stating how many respondents there are has named its base and has a thin
`population` answer. Folding countability into `base` would make one field answer two questions
and leave the corpus unable to express the common case where a base is clear and a sample is not.

So BCI reads `stated` with the gap recorded on `population`, where it belongs.

### 3. What the batch is, and is not

Nothing from it is written to `sources/audit.yaml`. The classifications were produced by targeted
text search over extracted text, which is strong enough to answer whether the property
discriminates and too weak to record under a `verified_against_artifact` basis. Recording them
would have been the false precision section 2 forbids, in the ADR that forbids it. The batch
answered its question and stopped.

### 4. The finding survives the narrowing, and is the more valuable half

**Publishers mostly state their base.** Cyentia names a denominator it cannot obtain. Verizon puts
`n=` on the figure and its base is *breaches*, not organizations. Bitkom labels twenty-six charts.
IBM labels its chart bases rather than leaving them inferred.

So the defect was never that the base is hidden. It is that the base lives in a chart label, a
footnote or a methodology page, and **the sentence that gets quoted does not carry it.** That is a
statement about how these reports are read, not about how they are written, and it is publishable
on its own. It is also why the narrowing costs little: a reader does not need fifty more `stated`
rows to be told that.

## Open questions

1. **Does the fifth question go to outside contributors?** ADR-0016 part 4 made the ask *read one
   source, answer four questions, twenty minutes*, and nobody has completed one yet. Adding a fifth
   before the four-question ask has ever been taken up would be tuning a route nobody has walked.
   Deferred until a first row arrives.
2. **Does `derivable` need the derivation recorded?** ADR-0008 requires `exceedance_detail` when a
   basis claims more than `none_known`, and the parallel suggests yes. Left open until the first 15
   reads show whether `derivable` is common enough to be worth the extra field.
