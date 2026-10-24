# ADR-0023 — The denominator becomes a declared property of an audited source

- **Status:** Proposed (2026-10-24)
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
  basis: stated | derivable | ambiguous | not_applicable
  publishes: <bool>
  verified_on: <ISO date>
  detail: <what the base is, in the report's own words where it names one>
```

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

## Open questions

1. **Does the fifth question go to outside contributors?** ADR-0016 part 4 made the ask *read one
   source, answer four questions, twenty minutes*, and nobody has completed one yet. Adding a fifth
   before the four-question ask has ever been taken up would be tuning a route nobody has walked.
   Deferred until a first row arrives.
2. **Does `derivable` need the derivation recorded?** ADR-0008 requires `exceedance_detail` when a
   basis claims more than `none_known`, and the parallel suggests yes. Left open until the first 15
   reads show whether `derivable` is common enough to be worth the extra field.
