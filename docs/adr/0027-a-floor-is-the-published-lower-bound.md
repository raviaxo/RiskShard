# ADR-0027 — A frequency floor is the published lower bound, band-matched to the org profile

- **Status:** Accepted (2026-11-20) — decided by the owner on the re-read finding
- **Date:** 2026-11-20
- **Deciders:** repo owner
- **Related:** [`0026-a-re-read-is-a-declared-property.md`](0026-a-re-read-is-a-declared-property.md)
  (the campaign that found it), [`0024-the-published-bracket.md`](0024-the-published-bracket.md)
  (the third instance of the same pattern — a banded table in a report we hold, unused),
  [`0007-construct-coherence.md`](0007-construct-coherence.md) (what quantity is being measured),
  [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md) (this is category one)

## Context

`frequency.min` on three shards — `au_finance_ransomware_midmarket`,
`de_industrial_ransomware_midmarket` and `jp_manufacturing_ransomware_midmarket` — was **0.10**,
drawn from Cyentia's IRIS Ransomware study and described in our own records as a *"global ransomware
likelihood floor"*.

The report says:

> "There's about a 10% **upper bound** chance that any given organization will experience at least
> one ransomware incident in the next 12 months."

and, on how the two estimates were built:

> "...one that yields high estimates (**upper bound**) and one that gives a **lower bound** ... the
> upper bound gives a more **risk-averse** view that we believe is generally better suited to
> managing risk."

**Our floor was the publisher's ceiling.** Figure 8's aggregate lower bound for at least one event
is about **0.49%**, against the 0.10 we used as a minimum — a factor of twenty, in the direction
that makes a shard look safer at its best case than the publisher's own conservative reading.

### How it happened, which matters more than that it did

**The publisher's summary page dropped the qualifier.** The page our records cite paraphrases the
finding as *"approximately 10% of organizations are likely to experience a ransomware incident
within the next year"* — no "upper bound", no mention that a lower bound exists. Our
`extraction_notes` copied that almost verbatim. The extraction was faithful to the document it read.
It read the wrong document.

This is the third time the [ADR-0024](0024-the-published-bracket.md) pattern has produced a finding,
and the cleanest statement of why the campaign is worth running: **the failure mode is not careless
reading, it is reading an accurate summary instead of the report.**

### The report publishes exactly what we needed

Table 3 gives the annual probability of one or more ransomware events **by revenue bracket, for both
bounds**. Every one of our three org profiles sits in a named bracket, and all three are above the
study's own $10M revenue cutoff (footnote 7), so the figures apply without stretching:

| shard | revenue | bracket | published lower | published upper | was |
| --- | --- | --- | --- | --- | --- |
| `au_finance_ransomware_midmarket` | USD 85,000,000 | $10M–$100M | **0.36%** | 11.32% | 10% |
| `de_industrial_ransomware_midmarket` | USD 120,000,000 | $100M–$1B | **1.20%** | 9.83% | 10% |
| `jp_manufacturing_ransomware_midmarket` | USD 130,000,000 | $100M–$1B | **1.20%** | 9.83% | 10% |

The old value was neither bound of either bracket.

## Decision

**A `frequency.min` anchored on a source that publishes a lower bound takes that lower bound, matched
to the org profile's own band where the source bands it.**

1. The three records move to **0.0036** (AU) and **0.012** (DE, JP), each citing Table 3 and naming
   its bracket.
2. Each record states **both** bounds, so the number a reader sees carries the width of the
   publisher's own uncertainty rather than one end of it.
3. `measurement_basis` stays `org_prevalence_loss_event` — the quantity did not change, only which
   published estimate of it we use.
4. **The upper bound is not adopted as a maximum here.** `frequency.max` on all three shards is
   anchored on country survey evidence (Bitkom for DE, and the equivalents for AU and JP) that
   measures the local population rather than a global model. Replacing a country-specific anchor
   with a global one would trade specificity for coherence, and that is a separate decision with its
   own evidence.

## Consequences

- **Three published frequency floors move**, and all three move **down**: 0.10 → 0.0036 and 0.10 →
  0.012. Annual loss figures fall accordingly at the low end. The shards do not become safer; they
  stop overstating their own best case.
- **The scenarios and calibrations are regenerated** rather than hand-edited, and the calibration
  rationale text now names the bound and the bracket instead of saying "floor".
- **A caveat gets louder**: each record now carries the upper bound too, and the fact that the
  publisher's page omits the distinction.
- **This is ADR-0009 category one** — it makes an existing published number more correct. No new
  axis, no new surface, no new machinery.

## Alternatives considered

- **Caveat only, move no value.** Record that 0.10 is the upper bound and leave it in place.
  Rejected: a minimum that is the publisher's maximum is not an undisclosed limitation, it is the
  wrong number. Disclosure is the remedy for a figure that is right but narrow.
- **Take the whole band row — lower bound as `min`, upper as `max`.** The most internally coherent
  option and the most disruptive, because it would overwrite country-survey frequency maxima with a
  global model. Declined under part 4 above, and recorded here so it can be argued separately
  rather than inherited.
- **Use the aggregate lower bound (~0.49%) for all three.** Simpler and worse: the report bands the
  figure, our profiles have revenue, and ignoring that is the exact omission this ADR exists to
  correct.

## Open questions

1. **Does `frequency.likely` deserve the same scrutiny?** It is country-survey-anchored on all three
   shards and was not examined here. Not decided; the re-read campaign will reach those records on
   their own sources.
2. **Should a source that publishes bounds be required to declare which one a record took?** This
   ADR does it in prose for three records. Whether it becomes a field is deferred until a second
   source makes the same demand.
