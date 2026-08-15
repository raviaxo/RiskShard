# ADR-0015 — The source audit: what a source publishes is not what we extracted

- **Status:** Accepted (2026-08-15)
- **Date:** 2026-08-15
- **Deciders:** repo owner
- **Related:** [`0007-construct-coherence.md`](0007-construct-coherence.md) (`measurement_basis`,
  the vocabulary this audits against), [`0008-the-governed-tail.md`](0008-the-governed-tail.md)
  (exceedance), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope gate), [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md) (the evidence
  object is the product)
- **Serves:** [finding 1](../FINDINGS.md), whose central claim is currently verified against **2**
  sources and asserted about the rest

## Context

Five findings on [`FINDINGS.md`](../FINDINGS.md) are separate measurements of our own corpus. Read
together they are one claim about something larger:

> The public cyber-loss evidence base does not publish the quantities that quantitative cyber risk
> models are built to consume.

- **0** anchors we hold are a mode, and no value in the 18-entry `measurement_basis` vocabulary
  denotes one — but a beta-PERT's second parameter *is* the mode, and three-point elicitation is
  the industry's standard shape.
- **0 of 11** impact ranges measure a single quantity.
- **2 of 11** maxima carry an exceedance statement.
- **7 of 66** parameters are drawn from the population they are used for.

Nobody has published that claim, and the parties best placed to are the least able: the commercial
loss databases are paywalled and commercially interested, and a vendor's number *is* its product.

**But the claim as it stands is stated about our corpus and implied about the field.** Finding 1
says *"no source consulted does"* and names direct verification of exactly two — NetDiligence 2025
and Verizon DBIR 2026. That is an honest sentence doing more work than its evidence supports, and
publishing it as a field-level audit without closing that gap would be the exact defect this
project exists to catch.

## The distinction this ADR exists to protect

There are two different facts, and conflating them is the failure mode:

- **What we extracted from a source.** Mechanically derivable today, from `evidence/` — every
  `measurement_basis` we took, every `exceedance_basis`, every population we declared.
- **What the source publishes.** Requires reading the source.

*"No record we hold from Sophos carries a distribution"* is a fact about **our extraction**. It is
not evidence that Sophos publishes no distribution — we may simply never have needed one. Deriving
the second from the first would produce a confident, checkable, wrong audit, and the error would be
invisible precisely because the derivation is mechanical.

This is the same error class as [finding 5](../FINDINGS.md), where a structured field asserted
something the prose beside it contradicted, and [finding 6](../FINDINGS.md), where a stored value
was read as intrinsic when it was relative. It has now appeared three times in this repository in
three different shapes. It gets a structural guard rather than a warning.

## Decision

**Audit the 61 registered sources on four properties. Every answer carries the basis on which it is
held, and a source-level claim may only rest on a source-level reading.**

### 1. The four questions

Asked of each source, because these are what a quantitative model consumes and what a practitioner
cannot tell from a citation:

| | |
| --- | --- |
| **mode** | Does it publish a most-likely / modal value — the beta-PERT parameter? |
| **distribution** | Does it publish a distribution or quantiles, or only point statistics? |
| **exceedance** | Does it state how often a loss of a given size is exceeded, over a named population? |
| **population** | Can the measured population be named from the source itself — country, sector, size? |

### 2. Every answer declares its basis, and the vocabulary is closed

- `verified_against_artifact` — a human read the stored artifact and this is what it says. **The
  only basis on which a claim about the source may be published.**
- `derived_from_corpus` — what our extraction shows. A fact about us, never about the source.
- `unverified` — not yet read. **The default, and it is not a defect; it is the work queue.**

A source-level statement (*"this source does not publish a mode"*) requires
`verified_against_artifact`. Anything else is reported as our extraction and labelled that way,
including in the published report.

### 3. Unverified is counted and published, not hidden

The audit's headline states its own coverage: how many of the 61 × 4 slots are verified. A reader
sees the denominator of our confidence before the finding. An audit that reports only what it
checked, without saying what it did not, is the thing this project was built to be the alternative
to.

### 4. It audits sources, and stops there

No ranking of sources, no quality score, no "best source for X", no recommendation. The output is
what each source publishes — a fact about the source — and the reader decides what that means for
their use. This is [ADR-0011](0011-fit-is-a-facet-set.md) part 2's refusal applied to a new object:
compressing four properties into a grade would assert a tradeoff we cannot make for someone else's
scenario.

Nor does it grade sources on *accuracy*. Whether Sophos's number is right is not in view; whether
Sophos publishes a mode is.

### 5. Scoped to the 61 registered sources, and the scope is stated in the claim

The corpus is **the sources a practitioner reaches for**, enumerated — not a census of public
cyber-loss evidence. No published sentence may imply otherwise. The enumeration is itself a
contribution, because no such list exists publicly; overstating it would forfeit the only thing
that makes the audit credible.

## Scope gate

[ADR-0009](0009-what-riskshard-is-and-is-not.md) asks: does this make an existing published number
more correct, or the method more sophisticated?

**More correct, and specifically.** [Finding 1](../FINDINGS.md) already publishes a claim about
what sources do and do not publish, resting on two direct verifications. This audit is the
measurement that claim should have rested on from the start. It introduces no modelling axis, no
new parameter, no new estimate, and changes no shard.

It does add a **new object** — a property of a source rather than of a parameter — which is why it
is recorded here rather than done as a docs change.

## Consequences

- **A finding gets a denominator.** "No source publishes a mode" becomes "of N sources read, 0
  publish a mode; M remain unread", which is weaker as a sentence and far stronger as a claim.
- **The work queue is the honest part.** 61 × 4 = **244 slots**, and most start unverified. That
  number is published, and it will look bad before it looks good.
- **It may refute finding 1.** If a read turns up a source publishing a modal value, the finding
  narrows and the correction is published like the others. The audit is not built to confirm what
  we already said.
- **It creates a maintenance obligation.** A source that publishes a new edition may change its
  answers, so verifications carry the artifact and date they were made against.

## Alternatives considered

- **Derive all four properties from `evidence/` and ship it this week.** Rejected — it is the
  conflation above, and it would be fast, mechanical, checkable and wrong.
- **Audit only the sources we extracted from (52 of 61).** Rejected: what a registered source
  publishes is interesting *especially* where we took nothing from it, and the nine unused sources
  are part of the enumeration.
- **Grade or rank sources.** Rejected under part 4.
- **Widen to the famous sources we do not hold** (Ponemon, Advisen/IRIS, Chainalysis, Marsh).
  Rejected for this pass on scope discipline — it converts a corpus audit into a source-hunting
  project. Recorded as a candidate once the 61 are read.

## Open questions

1. **Does an edition change invalidate a verification?** A verification names the artifact and date
   it was made against. Whether a new edition of the same title resets the answer, or carries it
   forward with a flag, is not decided here.
2. **Is "publishes a distribution" one property or two?** Quantiles at named percentiles and a
   fitted parametric distribution are different offers to a modeller. Treated as one for this pass;
   split if the reads show it matters.
