# ADR-0011 — Fit is a facet set, not a score

- **Status:** Accepted (2026-08-13)
- **Date:** 2026-08-13
- **Deciders:** repo owner
- **Prompted by:** John Flack (GRC Engineering Club `#labs_demos`, 2026-08-12), answering the
  question put to him on 2026-08-11 — the last open question on
  [ADR-0010](0010-where-riskshard-stops.md).
- **Related:** [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md) (this closes its
  open question 1), [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md)
  (`population_match`), [`0007-construct-coherence.md`](0007-construct-coherence.md)
  (`measurement_basis`), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope gate)

## Context

[ADR-0010](0010-where-riskshard-stops.md) recorded that the governed evidence object is the
product, and audited this repo against the field list a practitioner said such an object must
carry. One row came back **❌ not carried at all**: *how far it is from my context*. The ADR closed
with the question of where that even belongs, and put it back to the practitioner who supplied
the list:

> Does that live on the evidence object, or is it the analyst's job and our only duty is to give
> them enough to compute it?

He answered on 2026-08-12, and the answer has three parts.

**Distance is relative, so it cannot be a stored property.**

> *"I think the evidence object should carry enough structured context for 'distance' to be
> computed, but the distance itself only exists relative to a target."*

**Do not compress it into a number.**

> *"Would maybe avoid a single scalar-like score and instead expose the facets of fit n' mismatch:
> geography / sector / org size / control environment / measurement basis, blah blah blah . . .
> then the analyst can decide which mismatches matter for the scenario."*

**And a warning about our own vocabulary.**

> *"IMO, I think the 'product' is the governed evidence object that might inform a parameter. The
> parameter (again IMO) only really exists for us after someone applies their local context and
> modeling assumptions. Otherwise I think we risk sneaking portability back in through the word
> 'parameter' after just saying 'well, it ain't really portable'."*

That last point lands. ADR-0010 retired the "Metasploit for risk" analogy precisely because its
load-bearing claim was portability — and then went on using "parameter" for the thing being
offered, which carries the same implication more quietly.

### What checking our own schema found

The interesting part is not that we lack this. It is that **we already emit a facet set and did
not recognise it as one.**

`population_match` ([ADR-0003](0003-shared-impact-bridges.md)) stores
`status: matched | bridged` plus `bridged_on: [country | sector | size | threat]`. That is
literally a list of facets on which the record does *not* fit — not a score. The requested shape
already exists.

What is wrong with it is subtler and is exactly his point: **`population_match` is computed
relative to our shard's cell and then stored on the record as though it were a property of the
record.** A consumer reading `bridged_on: [country]` learns that the record was bridged on country
*for our target*, which tells them very little about *theirs*. The relativity is real but silent.

Meanwhile the raw material for the consumer's own computation is already required on every
record — `applicability` carries `industries`, `countries`, `company_size_bands` and `threats`,
and `measurement_basis` carries what was measured — but it is the *derived* fit we present
prominently, not the observed population it was derived from.

## Decision

**Fit is computed against a stated target and exposed as a facet set. It is never a score, and it
is never presented as a property of the evidence object alone.**

Three parts.

### 1. Distance is a function of two things, and we only own one

The evidence object's duty is to carry enough structured context that *any* consumer can compute
distance against *their* target. Computing it against our own shard cell is a convenience for one
consumer — us — and must be labelled as such wherever it appears, not presented as the record's
own attribute.

Concretely: `applicability` (the observed population) is the primary, target-independent fact and
must be surfaced at least as prominently as `population_match` (our derived fit). Today the
derived value is the visible one.

### 2. No composite fit score, ever

No single number, letter grade, or percentage summarising how well a record fits a target. Not as
a convenience, not as a sort key, not "just for the explorer." A scalar re-imports the portability
claim ADR-0010 retired: it asserts that the mismatches are commensurable and can be traded off
against one another by us, on the consumer's behalf, without knowing their scenario.

Facets are exposed individually and the consumer decides which ones bite. A geography mismatch is
fatal to one analysis and irrelevant to the next; only they know which.

### 3. "Parameter" stops being the word for the product

The governed evidence object is what this project offers. A *parameter* is what exists downstream,
after a consumer has applied local context and modelling assumptions. The repo's public vocabulary
must follow — the word may describe an input to our own reference rendering, but not the artefact
being published.

## Audit against the requested facets

| Facet | Carried? | Where |
| --- | --- | --- |
| geography | ✅ | `applicability.countries`; mismatch via `population_match.bridged_on: country` |
| sector | ✅ | `applicability.industries`; mismatch via `bridged_on: sector` |
| org size | ✅ | `applicability.company_size_bands`; mismatch via `bridged_on: size` |
| measurement basis | ✅ | `measurement_basis` (18 declared values, ADR-0007) |
| **control environment** | ❌ | **not carried, and this ADR does not authorize inventing it** |

Four of five requested facets already exist as structured fields. The gap is control environment,
and it stays a gap: `control_profiles/` exists but no evidence record declares the control
environment of the population it was measured on, because **published sources do not report it**.
Manufacturing one would be exactly the invented-responsiveness failure ADR-0009 and ADR-0010 both
refuse. It is recorded as a known absence, not scheduled as work.

## Scope

This clears [ADR-0009](0009-what-riskshard-is-and-is-not.md) without argument: it makes existing
published numbers **more correctly labelled**, it introduces **no fourth measurement axis**, and
it invents no data. Four of the five facets are already-carried fields that are under-surfaced —
the work is *surfacing and relabelling*, not measurement.

It also does not license the `org_profiles/` context work. That gap — six declared fields, none of
which affects any number — remains measured, elevated, and unscheduled, under the hard constraint
that any context dimension must be evidence-backed or it does not ship.

## Consequences

- **The front-door repositioning gets its design brief.** ADR-0010 made the evidence object the
  product without saying what its label looks like. It looks like this: the observed population,
  the measurement basis, and the mismatch facets — with fit stated relative to a named target.
- **`population_match` must be relabelled wherever it is rendered**, from a property of the record
  to a computation against our cell. The field itself does not change; its presentation does.
- **`applicability` gets promoted on reader-facing surfaces.** It is required on every record
  today and largely invisible.
- **A future consumer-supplied target is now a coherent feature rather than a guess** — "compute
  fit against *my* cell" is well-defined once fit is a function of a target. Not scheduled.
- **ADR-0010 open question 1 is closed.** Its audit row for *how far it is from my context* moves
  from ❌ *not carried at all* to **partially carried, wrongly framed** — four facets present,
  relativity silent, one facet absent.
- **This is the third framing corrected in six days** (the "numbers are inflated" claim, the
  module-library analogy, now "parameter"). That rate is what publishing your reasoning looks
  like, not instability.

## Alternatives considered

- **A composite fit score.** Rejected on the grounds above, and it is the option a reader would
  most expect — which is why the refusal is recorded rather than assumed.
- **Store the consumer's distance on the record.** Incoherent: there is no consumer at authoring
  time, and a record would need one value per possible target.
- **Treat it as fully the analyst's problem and change nothing.** Rejected — it is the reading his
  answer explicitly does not support (*"should carry enough structured context for distance to be
  computed"*), and we would keep presenting a derived, target-specific value as an intrinsic one.
- **Add `control_environment` to the evidence schema now.** Rejected: no source publishes it, so
  the field would be empty or invented.

## Open questions

1. **Does the target need to be a declared object?** Fit is relative to a target, and our target
   is currently implicit in the shard cell. Whether a consumer-supplied target profile becomes a
   first-class artefact is undecided and unscheduled.
2. **Does "when" deserve promotion too?** ADR-0010 marked it ⚠️ — `publication_date` and
   `extraction_date` are required, but the *observation period the measurement covers* is not a
   declared field. It is arguably a fit facet (a 2019 measurement is distant from a 2026 target)
   and is not addressed here.
