# ADR-0009 — What RiskShard is, and what it is not

- **Status:** Accepted (2026-08-08)
- **Date:** 2026-08-08
- **Deciders:** repo owner
- **Prompted by:** three strong external critiques in three days, each of which produced a new
  declared axis, and the fourth axis that arrived on 2026-08-08 and should not.
- **Related:** [`../PUBLISHABLE_REQUIREMENTS.md`](../PUBLISHABLE_REQUIREMENTS.md) → Change
  Control (the process this ADR is decided under),
  [`0006-depth-over-breadth.md`](0006-depth-over-breadth.md) (the same instinct, applied to
  coverage), [`0007-construct-coherence.md`](0007-construct-coherence.md),
  [`0008-the-governed-tail.md`](0008-the-governed-tail.md)

## Context

Between 2026-08-06 and 2026-08-08, three practitioners pushed on RiskShard from three
directions. Each critique was correct, each was acted on, and each produced a new declared
axis on every number in the repo:

| | axis | born from |
| --- | --- | --- |
| [ADR-0003](0003-shared-impact-bridges.md) | `population_match` — *who* was measured | a US-heavy source standing in for other cells |
| [ADR-0007](0007-construct-coherence.md) | `measurement_basis` — *what quantity* was measured | 18 of 22 ranges composing different quantities |
| [ADR-0008](0008-the-governed-tail.md) | `exceedance_basis` — what is known about being *exceeded* | 0 of 11 maxima carrying an exceedance probability |

On 2026-08-08 a fourth was proposed, in good faith and by the same practitioner whose question
produced ADR-0007: an `anchor_role` or `variation_source` axis — *not just what was measured,
but why is this number being allowed to occupy min/likely/max?* He flagged the risk himself:
*"that may be a little too navel-gazing, and if I'm inducing analysis paralysis, that doesn't
do your work any good."*

He was right to flag it, and the pattern is the point. Three axes in three days is a
trajectory, and the trajectory leads somewhere: a research project about how to measure cyber
risk. That is a legitimate thing to build. **It is not this thing**, and until now no document
said so — which is exactly why each suggestion had to be argued on its own merits, from
judgment, with nothing to test it against.

## Decision

**RiskShard is a governed evidence commons: useful, vetted, external data in an open-source
project, free to all. It is not a cyber-risk-quantification methodology project.**

Two obligations follow, and they are not symmetric.

### 1. Get CRQ right — always in scope

Anything that makes a **published number wrong** is a defect, and defects are fixed regardless
of cost or embarrassment. Being wrong about the quantitative method discredits the data, which
is the entire product. This is not negotiable and has no budget.

The 2026-08-08 finding is the worked example: a beta-PERT's second parameter is the **mode**,
and 7 of 11 shards feed a **mean** into it, while 7 of 11 use a central-tendency measure as the
**floor**. Two means, ordered by magnitude, labelled `min` and `likely`. That is not a
methodological preference — the distributions are mis-specified and the published numbers are
wrong. In scope, immediately.

### 2. Do not fix CRQ — out of scope, even when the idea is good

Improving the *discipline's* methods is not the mission. RiskShard may adopt a better method
when a defect forces it, but it does not set out to advance the state of the art in
quantification, and it declines work whose value is a more sophisticated model rather than a
more trustworthy number.

### The test

> **Does this change make an existing published number more correct — or does it make the
> method more sophisticated?**

First is in scope. Second is not. When a proposal is genuinely both, it is in scope only to the
extent needed to fix the number, and the remainder is declined and recorded.

### The rule for new axes, specifically

**An axis may only be born from a defect measured in our own data — never from a good idea
about measurement.**

This retro-justifies all three existing axes: each was proposed *after* the defect was found
and counted (a population mismatch, 18 mixed ranges, 0 exceedance statements). It forbids a
fourth proposed in the abstract, however sound. It also supersedes the narrower argument in
[ADR-0008](0008-the-governed-tail.md) that "three axes is the ceiling" — the number was never
the point; provenance of the proposal is.

## Consequences

- **Good suggestions will be declined.** `anchor_role` is the first: the question *why does
  this number occupy this slot?* is a fair one, and the answer already has a home — the
  per-parameter `rationale` in each calibration profile, as prose. That is the cheap version
  that informs a reader without adding a vocabulary, a gate and two surfaces.
- **Declined is not ignored.** A declined proposal is recorded with its reason, here or in
  `NEXT_STEPS`, so a contributor can see it was weighed. Silence would read as dismissal and
  would cost the exact relationships that produced the last three improvements.
- **The correctness bar goes up, not down.** Narrowing scope is not permission to be
  approximate. It concentrates the effort: fewer axes, and no tolerance at all for a number
  that is wrong.
- **"Free to all" is part of the definition, not a footnote.** Where two paths are otherwise
  equal, prefer the one that makes the data more usable and citable by an outsider over the one
  that makes the model cleverer. That is the tie-breaker.
- **Agents get a test they can apply without the owner.** The absence of this document is why
  every strong external prompt escalated to a judgment call. It should now resolve most of them.

## Alternatives considered

- **Become the methodology project.** Rejected. That layer is crowded and well-served, and the
  defensible position was never the engine — it is the governed evidence nobody else publishes.
  See [`../internal/canonical_reference_thesis.md`](../internal/canonical_reference_thesis.md).
- **Say nothing and keep deciding case by case.** Rejected: that is the status quo that
  produced three axes in three days, each individually justified and collectively a drift.
- **Cap the number of axes.** Rejected as arbitrary — it was ADR-0008's formulation and it is
  the wrong discriminator. A fourth axis born from a measured defect in our own numbers would
  be correct to build; a third born from a good idea would not have been.
