# ADR-0008 — The governed tail: a maximum must say what it bounds

- **Status:** Accepted (2026-08-07) — decision taken; **implementation not started**, see *Scope*
- **Date:** 2026-08-07
- **Deciders:** repo owner
- **Prompted by:** three independent external critiques within four days, which turned out to
  be three faces of one defect — see *Context*
- **Related:** [`0007-construct-coherence.md`](0007-construct-coherence.md) (this answers half
  of its open question 1), [`0005-documented-loss-event-registry.md`](0005-documented-loss-event-registry.md)
  (Deferred — this ADR gives it a reason to come back),
  [`0006-depth-over-breadth.md`](0006-depth-over-breadth.md) (confirmed from outside),
  [`../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md`](../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md)

## Context

Between 2026-08-06 and 2026-08-07 three people who do not know each other pushed on RiskShard
from three directions:

- **John Flack** (GRC Engineering Club) asked how to test whether a range's three anchors
  measure comparable things. That became [ADR-0007](0007-construct-coherence.md):
  **4 coherent · 18 mixed** of 22 parameter families, and *no impact family coherent*.
- **Old_Positive2231** (r/GRC) pushed for dogfooding — publish worked decisions, with the
  decision impact shown. That became
  [the AU ransomware limit decision](../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md).
- **Adrian Sanabria** ([destroyedbybreach.com](https://destroyedbybreach.com/)) published an
  index of the 35 organisations known to have died from a cyber incident, 2002–2026. It carries
  **no dollar figures at all** — see [the scout note](../internal/destroyed_by_breach_scout.md).

Read separately, that is one methodology critique, one distribution critique, and one adjacent
project. Read together, all three are about the **maximum**.

### The defect, in the repo's own data

Measured 2026-08-07 across the calibration-selected anchors of all 11 shards. Reproduce with
`python scripts/riskshard_modules.py coherence`.

| anchor | what it measures, portfolio-wide |
| --- | --- |
| `impact.likely` | a central tendency in **11 of 11** — 8 `mean_total_event_cost`, 3 `cost_component` |
| `impact.max` | a modeled quantile in **0 of 11** — 4 `single_documented_event_loss`, 4 `observed_extremum`, 2 `statutory_penalty_cap`, 1 `regulatory_penalty_issued` |
| `frequency.likely` | `org_prevalence_incident` in 10 of 11 |
| `frequency.max` | `org_prevalence_incident` in **11 of 11** — the same *kind* of number as `likely` |

Two facts follow, and neither was visible before `measurement_basis` existed:

1. **Not one `impact.max` in the portfolio carries an exceedance probability.** Every one is
   either something that happened once, the largest row in somebody's dataset, or a legal
   ceiling. None of them answers "how often is a loss worse than this?" — which is the only
   question a maximum is asked in a risk decision.
2. **The stress case is not a worse year; it is a bigger reading.** Every `frequency.max` is the
   same construct as its `frequency.likely`, sampled from a different survey. The portfolio's
   entire notion of "stress" is a larger survey number plus one anecdote.

### Why this is not cosmetic

[The worked decision](../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) measured the cost of (1) on a
real question — what insurance limit should an Australian mid-market finserv firm buy:

- the per-event mean is **14.8× its own mode**, because the `single_documented_event_loss` at
  `impact.max` **drives** the distribution's mean rather than bounding it;
- changing **only that one anchor** swings **P(event > AUD 20M) from 0% to 23%**.

So the anchor with no probability attached to it is the anchor the answer is most sensitive to.
The number a reader would treat as the safe outer bound is the number doing the most work and
carrying the least evidence.

### What Sanabria has

`destroyedbybreach.com` is the missing half. It has no dollars — but 35 organisations across 24
years and 12 countries is an **exceedance statement for the fatal tail**: roughly once or twice
per year, globally. That is exactly the quantity our maxima lack, held by someone who lacks the
quantity our maxima have.

## Decision

**RiskShard's unit of value becomes the governed tail.** The claim it earns the right to make is
narrow and checkable: *this is the only open CRQ substrate that tells you what its maximum means,
and what your decision does when that maximum moves.*

Three commitments follow.

### 1. A maximum must declare what it bounds

A third declared axis, orthogonal to the two that exist. ADR-0003's `population_match` answers
*who was measured*. ADR-0007's `measurement_basis` answers *what quantity was measured*. This
answers **what, if anything, is known about being exceeded**:

| `exceedance_basis` | meaning |
| --- | --- |
| `modeled_quantile` | a stated percentile of a fitted or published loss distribution |
| `observed_rank` | the k-th largest of N observations, so an empirical exceedance of k/N can be stated |
| `population_ceiling` | a legal or contractual bound — exceedance under that head of loss is defined as zero, and carries no frequency information |
| `none_known` | one documented event, or an extremum with no stated N. **No exceedance statement is available.** |

`none_known` is a legal value and, today, the honest one for most of the portfolio. It is not a
placeholder to be quietly cleared. What changes is that it must appear **on the face of the
number**, in the same breath as the value: *this is the largest loss we found, not the largest
loss that can happen; nothing here says how often it is exceeded.*

This answers the half of [ADR-0007 open question 1](0007-construct-coherence.md#open-questions--deliberately-not-decided-here)
that does not need John: *does a `single_documented_event_loss` need a stated exceedance
probability to belong in a range?* **It needs a stated exceedance basis, and `none_known` is an
acceptable one — declared, never silent.** Which *mixes* are acceptable remains his question and
is still open.

### 2. Tail sensitivity becomes an output, not a one-off

The 14.8× and the 0%→23% were computed by hand for one shard. Every shard has the same shape and
therefore the same exposure. A shard's tail sensitivity — what the decision does when `impact.max`
alone is moved — becomes a first-class readout rather than a finding in a document.

### 3. Base rates are the evidence objective that reopens

The evidence map was declared finished on 2026-08-03 "as far as public data allows", and that
stands **for severity**. It was never true for exceedance, because nothing in the repo was
looking for it. [ADR-0005](0005-documented-loss-event-registry.md) was Deferred for want of a
second maintainer; a documented loss-event registry is precisely an exceedance denominator, and
Sanabria has both the dataset and the open question. That changes the ADR-0005 calculus and it
should be revisited on those grounds, not resurrected on the old ones.

## Scope

**Decided here:** the direction, the third axis and its vocabulary, and the three commitments.

**Not built here.** No field, gate, surface or CLI ships with this ADR. `v0.5.0` carries the
decision, not an implementation. Implementation is the next objective and follows the ADR-0007
shape: declare on every `impact.max` first, surface it on the explorer and the evidence report
second, decide gating third. Sequencing and the fact that nothing is built yet are recorded in
[`../internal/NEXT_STEPS.md`](../internal/NEXT_STEPS.md).

## Consequences

- **The headline gets worse again, and this is the third time.** ADR-0003 disclosed the
  population mismatch; ADR-0007 disclosed 18 of 22 families mixed; this discloses **0 of 11
  maxima with a stated exceedance**. Each disclosure made the portfolio read weaker and the
  repo more trustworthy. That is the trade, taken deliberately, per
  [`../PUBLISHABLE_REQUIREMENTS.md`](../PUBLISHABLE_REQUIREMENTS.md) — caveats get louder, not
  quieter.
- **Three axes is the ceiling, not a pattern.** The obvious objection is that lenses can be
  invented indefinitely. This one is not arbitrary and the difference is measurable: it is the
  axis the engine's own output is most sensitive to — 14.8× the mode, 0%→23% on a real decision.
  A fourth axis needs the same kind of evidence before it is added.
- **`none_known` will be the common answer for a long time.** Published loss distributions with
  tail quantiles are rare, and the ones that exist are commercial. The value of declaring it is
  not that it gets fixed; it is that a reader stops mistaking an anecdote for a bound.
- **Positioning sharpens rather than shifts.** The moat was already provenance, not the engine.
  This names the specific provenance nobody else publishes. It does not require a new engine, a
  new shard, or a new country — consistent with [ADR-0006](0006-depth-over-breadth.md), which
  three independent critics have now confirmed from outside: not one of them asked for more
  coverage.
- **The two queued owner discussions stay deprioritized.** FTC-UDAP sources and
  compliance-impact shards are both more coverage. They fall further behind, not closer.

## Alternatives considered

- **Ship worked decisions as the unit of value** (Old_Positive2231's pull, taken literally).
  Rejected as the *primary* move for a specific reason: those decisions would rest on exactly the
  maxima this ADR shows to be unevidenced, so scaling the output would scale a known defect.
  Worked decisions remain how the tail work is *demonstrated* — commitment 2 exists because the
  first one was so productive — but they are the vehicle, not the foundation.
- **Close ADR-0007 open question 1 first and stop there.** Narrower and cheaper, but it waits on
  an external reply and answers one critic of three, leaving the maximum un-probabilised.
- **Record the finding and change nothing.** Rejected: three independent experts pointed at the
  same joint within four days, and the repo's own instrumentation confirmed it at 0 of 11.
