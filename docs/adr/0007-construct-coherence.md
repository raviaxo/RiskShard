# ADR-0007 — Declared measurement basis and range coherence

- **Status:** Proposed (2026-08-07) — **still Proposed as of 2026-08-22, deliberately.** Parts 3
  and 4 remain open and open question 1 carries a standing recommendation awaiting the owner. A
  restriction on composed answers is recorded below (*Standing restriction*) so that work is not
  blocked on a decision that is not mine to take.
- **Date:** 2026-08-07
- **Deciders:** repo owner
- **Scope proposed:** declare a `measurement_basis` on every evidence record (part 1) and
  report, per parameter family, whether a shard's selected anchors share one basis (part 2).
  Parts 3 (deciding which mixes are acceptable) and 4 (gating in CI) are **not** proposed
  here and are deliberately left open — see *Open questions*.
- **Prompted by:** John Flack (GRC Engineering Club, 2026-08-06), who asked how to test
  "not only whether a parameter is source-backed, but whether the three anchors are
  measuring sufficiently comparable things to belong in the same distribution."
- **Related:** [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md) (the
  population axis), [`../METHODOLOGY.md`](../METHODOLOGY.md)

## Context

ADR-0003 established that every source-backed record declares **who** was measured — its
`population_match`, and the dimensions it is bridged on. That closed a real gap: a US-heavy
or disclosure-biased source standing in for another country, sector or size band is now
labelled, and the caveat rides inside any citation of the number.

It does not close a second, independent gap. `population_match` answers *who was measured*.
It says nothing about *what quantity was measured*. Two anchors can both be full-cell
matches for a shard and still be different random variables.

The engine composes `min`, `likely` and `max` into a single triangular distribution. That
composition is only meaningful if the three anchors measure the same quantity. Nothing in
the schema, the validator or the readiness tooling has ever checked that they do.

### The defect, in the repo's own data

Measured 2026-08-07 across the calibration-selected anchors of all 11 shards.

`gb_finance_data_breach_midmarket` is the clearest case, and it is the shard the portfolio
reports as **fully cell-matched** — `population_match: matched` on all six parameters:

| anchor | value | what it actually measures |
| --- | --- | --- |
| `impact.min` | GBP 10,000 | DSIT top-5% **perceived** cost, self-reported by survey respondents |
| `impact.likely` | GBP 5,740,000 | IBM **average total** breach cost, activity-based costing |
| `impact.max` | GBP 11,164,400 | The Equifax **regulatory penalty** issued by the FCA |

Three different quantities. Each is correctly sourced, correctly cited, correctly caveated,
and full-cell matched. The range built from them is not a distribution of anything.

The same pattern recurs:

- **`fr_finance_data_breach_midmarket`** and **`au_finance_data_breach_midmarket`** put a
  **statutory penalty cap** (GDPR Article 83(5), Privacy Act s13G(3)) at `impact.max`. A
  legal ceiling is not an observed loss and has no sampling relationship to the mean.
- **`sg_finance_bec_midmarket`** frequency runs *reported police cases ÷ enterprise count*
  (0.001) → *organisation prevalence of BEC activity* (0.63) → *organisation prevalence of
  **any** cyber incident* (0.80). Three constructs; the 800× span between floor and mode is
  mostly construct, not uncertainty.
- **`au_finance_bec_midmarket`** `impact.max` is AUD 2.0M, the ACCC's **national aggregate**
  of small-business false-billing losses for the year. An aggregate across a population is
  being used as one organisation's tail loss. *(**Corrected 2026-08-07** — this was the last
  construct-inappropriate anchor and the one the owner's decision on open question 2 did not
  excuse. It now reads AUD 2,668,483, one documented Australian BEC event reported by the AFP;
  see the [revision](../../revisions/2026-08-07-australia-bec-stress-anchor-moves-to-a-documented-event.yaml).
  The family stays `mixed`, which is the point: the fix was construct-appropriateness, not
  coherence.)*
- The ransomware shards (**AU**, **JP**, **DE**) anchor `frequency.min` to a
  **loss-event** prevalence (Cyentia IRIS) and `likely`/`max` to **attack** prevalence
  (Sophos, Bitkom). Every record says so in prose; nothing makes it structural.

A second and third class appear alongside it, both invisible to `population_match`:

- **Strata as spread.** GB, FR and US-DB frequency use *different size bands of one
  cross-section* as min/likely/max (all-business → medium → large). The width encodes
  between-group variation, not uncertainty about the shard's own cell.
- **Vintage as spread.** CA frequency is StatCan 2019 / 2023 / 2021; AU and JP are Sophos
  2024 / 2023. The width is a short time series. CA is the portfolio's proudest full-cell
  match and is affected.

This is the same shape of defect ADR-0003 addressed, on a different axis, and it was found
the same way: from outside, by a practitioner reading the published record.

## Decision

**Part 1 — declare the basis.** Every evidence record carries a `measurement_basis` drawn
from a controlled vocabulary. The vocabulary is deliberately about the *quantity measured*,
not the source or the method of collection — those are already covered by `source_type` and
`population_match`.

Frequency-side bases:

| term | meaning |
| --- | --- |
| `org_prevalence_incident` | share of organisations with ≥1 incident of the named type in the period |
| `org_prevalence_loss_event` | share of organisations with ≥1 event of confirmed financial loss |
| `org_prevalence_threshold` | share of organisations with ≥N incidents, N > 1 |
| `reported_case_rate` | reported cases, complaints or notifications ÷ a population denominator |
| `event_rate_per_entity` | events per entity per period; a count, may exceed 1 |
| `attribution_share` | share of events attributable to a named cause |
| `conditional_probability` | probability of a stage given a prior event (loss chains) |

Impact-side bases:

| term | meaning |
| --- | --- |
| `mean_total_event_cost` | mean total cost per event |
| `median_total_event_cost` | median total cost per event |
| `cost_component` | a named subset of total cost (crisis services, restoration, ransom paid, recovery excluding ransom) |
| `single_documented_event_loss` | the loss from one named, documented incident |
| `perceived_cost_self_reported` | cost as estimated by a survey respondent, not measured |
| `observed_extremum` | maximum or extreme band of an observed dataset |
| `statutory_penalty_cap` | a legal maximum; not an observed loss |
| `regulatory_penalty_issued` | a penalty actually levied by a regulator |
| `aggregate_population_loss` | total loss across a population, not per event |

Shared:

| term | meaning |
| --- | --- |
| `interpretive_estimate` | not a reported statistic; a labelled modelling judgment |
| `context_statistic` | supporting evidence that never anchors a range (a `context.*` parameter) |

**Part 2 — report coherence separately.** For each shard and each parameter family
(`frequency`, `impact`, and each loss stage), the tooling reports the set of distinct bases
across the calibration-selected anchors:

- `coherent` — all selected anchors share one basis.
- `mixed` — two or more bases, **named**, in the same way `population_match` names the
  bridged dimensions.

This is a declaration, not a verdict. `mixed` is not automatically an error — a median floor
under a mean mode may well be defensible. What is not defensible is it being invisible.

## Measured result (2026-08-07)

All 141 evidence records annotated; `scripts/riskshard_modules.py coherence` reports:

> **4 coherent · 18 mixed** of 22 parameter families across 11 shards.
> **All 11 shards carry at least one mixed family. No impact family is coherent — all 11 are mixed.**

The four coherent families are worth reading closely, because they are the finding:

| shard | family | basis |
| --- | --- | --- |
| `ca_finance_data_breach_midmarket` | frequency | `org_prevalence_incident` |
| `fr_finance_data_breach_midmarket` | frequency | `org_prevalence_incident` |
| `gb_finance_data_breach_midmarket` | frequency | `org_prevalence_incident` |
| `us_finance_data_breach_midmarket` | frequency | `org_prevalence_incident` |

Every one of them passes the construct test **because its spread comes from somewhere else
entirely**: GB, FR and US-DB are size strata (all-business → medium → large), CA is a survey
vintage series (2019 → 2023 → 2021). They are coherent on the axis this ADR measures and
questionable on an axis nothing measures yet. That is the strongest available argument for
open question 3.

Three anchors were revealed as construct-inappropriate rather than merely mixed. **The owner
subsequently ruled two of the three deliberate** (open question 2, decided 2026-08-07); only the
first remains a defect:

- `au_finance_bec_midmarket` `impact.max` — AUD 2.0M, the ACCC's **national aggregate** of
  small-business false-billing losses, standing in for one organisation's tail loss
  (`aggregate_population_loss`, a basis that should never anchor a range).
- `fr_finance_data_breach_midmarket` and `au_finance_data_breach_midmarket` `impact.max` —
  statutory penalty caps carrying no likelihood information.

These are corrections, not declarations, and are queued as their own objective rather than
folded in here.

## Consequences

- The public headline gains a second axis and it will read worse than the first. That is the
  same trade ADR-0003 took, for the same reason.
- `population_match: matched` stops implying a number is safe to combine. The two axes must
  be read together, and the explorer and evidence report must present them together.
- Records already carry the information in prose — nearly every affected record names its own
  construct limitation in `limitations` or `normalization_notes`. This ADR makes it
  structural, sortable and countable rather than a paragraph a reader has to notice.
- Some anchors will be revealed as construct-inappropriate rather than merely mixed — the
  ACCC aggregate at `au_finance_bec` `impact.max` is the clearest. Those are corrections, and
  they follow the normal `revisions/` path.

## Standing restriction — 2026-08-22: composed answers borrow, they do not assemble

Parts 3 and 4 were left open on 2026-08-07 because nothing depended on them. Something does now: a
design that composes an answer for a named cell has to decide **where its anchors come from**, and
the two available routes are not equally exposed to this ADR's open questions.

**Nearest-shard borrowing is permitted.** It takes an existing shard's anchor set whole and marks
what was borrowed. Whatever coherence that set has, this ADR has already measured it — the shard
appears in the 4-coherent/18-mixed table above, and its mixed families are already declared on the
item's face. Borrowing moves a *population* boundary, which is ADR-0003's axis and is already
labelled. It does not create a construct combination that has never been looked at.

**Best-anchor-per-parameter assembly across the corpus is not permitted while parts 3 and 4 are
open.** Selecting the best-fitting `impact.min` from one shard, `impact.likely` from another and
`impact.max` from a third builds a range whose three anchors may each measure a different quantity
over a different population — and unlike a shard, that combination has never been through the
coherence report, because the report runs per shard and the composed cell is not a shard. The
measured result above is the reason this is not theoretical: **all 11 shards already carry at least
one mixed family, and no impact family is coherent in any of them.** Assembly would compound a
defect that is currently universal rather than avoid it.

This is a restriction, not a decision. It costs the better numbers assembly would produce, and it
lifts the moment parts 3 and 4 close — or the moment a composed cell can be run through the
coherence report the way a shard is, which is the cheaper of the two routes and is not scheduled.

**Owed to the owner:** open question 1 below has carried a recommended closure since 2026-08-09 —
John Flack's own reframing, that no mix is acceptable or unacceptable in general, that our duty is
to label, and that admission is the consumer's call. It is consistent with
[ADR-0010](0010-where-riskshard-stops.md). Closing it is the owner's call and it has been open for
two weeks; the residue if it closes on those terms is the labelling duty named there, which this
ADR has not discharged.

## Open questions — deliberately not decided here

These are the judgment calls, and they are published rather than resolved quietly:

1. **Which mixes are acceptable?** Is `median_total_event_cost` → `mean_total_event_cost`
   an acceptable floor-to-mode pairing? ~~Is a `single_documented_event_loss` a legitimate tail
   anchor, or does it need a stated exceedance probability to belong in the range?~~ **The tail
   half is DECIDED 2026-08-07 (owner) in [ADR-0008](0008-the-governed-tail.md): it needs a
   stated *exceedance basis*, and `none_known` is an acceptable one — declared, never silent.
   Measured across the portfolio, `impact.max` carries a modeled quantile in 0 of 11 shards.**
   Which *mixes* are acceptable remains open and remains John's question.

   *Asked of him directly and declined twice — 2026-08-07, where he reframed it (the problem is
   not which mixes are acceptable, it is why a number is allowed to occupy a slot at all), and
   2026-08-09, where he relocated the decision entirely: the evidence object declares what it
   is, and **the analyst owns whether it belongs in the model, how it is transformed, and what
   structure it goes into**. Read straight, that dissolves the question rather than answering
   it — no mix is acceptable or unacceptable in general, our duty is to label, and admission is
   the consumer's call. That reading is consistent with
   [ADR-0010](0010-where-riskshard-stops.md) and is **recommended for closure on those terms**.
   Left open here because closing an ADR question is the owner's, and because a declared
   `mixed` range still owes its reader a plain statement of what the mixing does to the
   number — which is a labelling duty this ADR has not discharged.*
2. ~~**Should a statutory cap ever anchor `impact.max`?**~~ **DECIDED 2026-08-07 (owner): yes —
   a statutory cap may anchor `impact.max`.** Dropping it would lose the only evidence of the
   regulatory tail, and the cap is a real, citable bound. The condition is that it stays
   *declared*: `statutory_penalty_cap` is its own basis, the range reads `mixed` because of it,
   and the reader is told on the item's face that a legal ceiling carries no information about
   likelihood. `fr_finance_data_breach_midmarket` (GDPR Art. 83(5), EUR 20M) and
   `au_finance_data_breach_midmarket` (Privacy Act s13G(3), AUD 50M) therefore **stand as
   deliberate methodological choices, not defects**, and leave the correction queue. The cost is
   now measured rather than assumed: see
   [the worked decision](../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) — a maximum carrying no
   exceedance probability does not merely bound a PERT, it drives its mean.
3. **Strata-as-spread and vintage-as-spread** — are these a third and fourth declared status,
   or a note on the calibration rather than the record?
4. **Does this gate?** ADR-0003 part 2 reports without gating. The calibration-drift check
   gates. Coherence could do either.

Question 1 is the one that decides the rest.
