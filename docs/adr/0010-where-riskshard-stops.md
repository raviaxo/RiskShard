# ADR-0010 — Where RiskShard stops: the evidence object is the product

- **Status:** Accepted (2026-08-11)
- **Date:** 2026-08-11
- **Deciders:** repo owner, stated publicly in GRC Engineering Club `#labs_demos`
- **Prompted by:** John Flack (GRC Engineering Club, 2026-08-09), answering the parameter-spec
  question put to him on 2026-08-08 — and arguing, unprompted, that the project should stop
  before quantification.
- **Related:** [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope: commons, not methodology — this ADR finishes the sentence it started),
  [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md),
  [`0007-construct-coherence.md`](0007-construct-coherence.md),
  [`0008-the-governed-tail.md`](0008-the-governed-tail.md)

## Context

On 2026-08-08 the owner committed publicly, in GRC Engineering Club `#labs_demos`: *"The Monte
Carlo on the front page is a demo of what the evidence implies, not the product — though that's
not obvious from how it's presented, which is mine to fix."*

That repositioning was deliberately gated on one outstanding answer: **what must a parameter
carry for a practitioner to use it without wincing?** Designing the front door without it would
have been guessing at the thing the front door exists to present.

The answer arrived 2026-08-09 and did three things.

**It gave the field list.** A governed evidence object should carry: *what was observed · who it
was observed on · when · how it was measured · what statistical role it really has · how far it
is from my context · and what it can't end up supporting.*

**It retired our own framing.** The "Metasploit for risk — a vetted module library" analogy,
said publicly by the owner on 2026-08-08, does not survive contact:

> *"An exploit module is relatively stable once you know the target conditions. Risk observation
> doesn't stay portable in quite the same way because the org, controls, threat environment,
> dependencies, and time horizon are part of the thing you're trying to estimate."*

This is correct, and it is not a quibble about metaphors. The analogy's whole load-bearing claim
was portability — take the module, know your target conditions, run it. For a risk observation
the target conditions *are* the estimand, so there is no residue left over that travels. The
more we separate population match, measurement basis, anchor role and local context, the *less*
these look like pluggable parameters, not the more. Separating them is still right; calling the
result a module library was not.

**It argued for doing less.** *"The project might get stronger by doing a little less: be
exceptionally amazing at governing external evidence and making its limits explicit, and let the
actual quantification happen downstream… the provenance/evidence layer is increasingly the part
I'd end up trusting most, so I'm not sure it needs to also carry a burden of being a generic
risk engine."*

The same practitioner also declined the other question outstanding with him — what fraction of a
real analysis can legitimately come from outside the org — as the wrong one to worry about:
*"I do end up worrying less around '5% or 40%' and more where RiskShard stops."*

Independently and on the same day, Adrian Sanabria — who maintains
[Destroyed by Breach](https://destroyedbybreach.com) — described the same problem from the
supply side: breach reporting is inconsistent, a second public dataset carries financial figures
but collects them automatically "so it isn't always correct", and his own loss data is
inconsistent too. Two practitioners, two conversations, no contact between them, one conclusion:
**the loss data exists and nobody governs it.**

## Decision

**The governed evidence object is the product. The simulation is a reference rendering of it,
and it comes off the front door.**

Stated publicly by the owner in `#labs_demos` on 2026-08-11: *"The parameter is the product and
the simulation is one rendering of it, so it comes off the front door."* This ADR records that
commitment rather than originating it.

Three parts follow.

### 1. The engine is demoted, not deleted

RiskShard stops at governed evidence with its limits declared. Quantification is the consumer's
step: whether the evidence belongs in their model at all, how it should be transformed, what
local data overrides it, and what distribution or scenario structure fits.

The engine stays in the repository for one reason, and it is not sentiment: **it is the
mechanism that finds our own defects.** The tail-sensitivity table — the strongest artifact this
project has for the "so what?" question — exists only because there is a simulation to be
sensitive. The mis-specification counted in [ADR-0009](0009-what-riskshard-is-and-is-not.md)
obligation 1 (8 of 11 shards passing a mean into a mode slot) is visible only because something
composes those anchors into a distribution. Delete the engine and the evidence layer loses its
best critic.

So: kept, exercised, published as a worked rendering — and never again presented as the thing
being offered.

### 2. The module-library framing is retired

The "Metasploit for risk" analogy is withdrawn, publicly, by the person who made it publicly.
Recorded here so it is not quietly reintroduced by a future reader who finds it in the
2026-08-08 session record and mistakes it for the current thesis.

What replaces it is narrower and survives the objection: **a governed observation with its
distance from you declared.** Not portable. Labelled well enough that you can decide whether it
travels.

### 3. The evidence object's required label is that field list — and we are audited against it

| The label must carry | Status in this repo |
| --- | --- |
| what was observed | ✅ `measurement_basis` ([ADR-0007](0007-construct-coherence.md)) |
| who it was observed on | ✅ `population_match` ([ADR-0003](0003-shared-impact-bridges.md)) |
| when | ⚠️ present in the source record, not a declared field |
| how it was measured | ✅ `measurement_basis` ([ADR-0007](0007-construct-coherence.md)) |
| **what statistical role it really has** | ❌ **carried wrongly** — 8 of 11 shards pass a published mean into the mode slot; 7 of 11 use a central-tendency figure as the floor |
| **how far it is from my context** | ⚠️ **partially carried, wrongly framed** — four of five facets exist as fields (`applicability`, `population_match`, `measurement_basis`); fit is presented as a property of the record rather than as a computation against a target, and control environment is absent. Specified in [ADR-0011](0011-fit-is-a-facet-set.md) *(was ❌ not carried at all, corrected 2026-08-13)* |
| what it can't end up supporting | ⚠️ declared for the tail only ([ADR-0008](0008-the-governed-tail.md)) |

This is a *labelling* specification, not a new measurement axis. It ratifies the three declared
axes and names what is missing beside them.

## Consequences

- **The front-door repositioning is unblocked and now owed twice.** It was gated on this answer;
  the answer arrived and went further than the question. It is the next objective after the
  anchor-slot correction, and it now has an external design brief rather than a guess.
- **The anchor-slot objective is unchanged and externally re-motivated.** "What statistical role
  it really has" is precisely the defect already queued. Fixing it now also closes a line on the
  label. Scope discipline from ADR-0009 still binds: no fourth axis, no invented modes, and
  where a source publishes only a mean, say so on the record and leave it.
- **The context gap is elevated, and it clears the ADR-0009 gate.** "How far it is from my
  context" is the same hole measured in our own data on 2026-08-08: `org_profiles/` declares six
  fields — revenue, employees, data sensitivity, internet exposure, third-party dependency,
  regulatory intensity — and **not one affects any number**. It therefore qualifies under
  ADR-0009's rule that an axis may only be born from a defect measured in our own data. It
  qualifies; it is not thereby scheduled. And the hard constraint stands: any context dimension
  must be evidence-backed like everything else, or it does not ship. A multiplier invented to
  make the model feel responsive is exactly what this project exists to refuse.
- **Do not read "do less" as "do less carefully."** Narrowing to the evidence layer raises the
  bar on that layer. Everything the engine used to absorb — an anchor that is nearly right, a
  caveat that lives in prose — is now load-bearing on its own.
- **A public retraction is cheap and should stay cheap.** This is the second framing withdrawn
  in three days (after the "numbers are inflated" claim on 2026-08-08). That rate is a feature
  of a project that publishes its reasoning, not evidence of instability.

## Alternatives considered

- **Delete the simulation engine entirely**, as the strict reading of "let quantification happen
  downstream" implies. Rejected — it removes the mechanism that produced every defect this
  project has caught in itself, including the one currently queued. Demotion achieves the
  honesty without the loss.
- **Defend the module-library framing.** Rejected. The portability claim is the analogy's whole
  content and the objection lands squarely on it.
- **Keep the front door as it is** and treat the 2026-08-08 commitment as satisfied by a caveat.
  Rejected — a caveat under a headline percentile is the thing that was called out in the first
  place.
- **Wait for a second opinion before recording this.** Rejected: the decision was already stated
  in public. An unrecorded public commitment is how the queue starts lying, which this project
  has now caught itself doing once.

## Open questions

1. ~~**Where does "how far it is from my context" live?** On the evidence object, or is it the
   consumer's computation and our duty is only to give them enough to compute it? Put back to
   John Flack on 2026-08-11; unanswered.~~
   **✅ ANSWERED 2026-08-12 — closed by [ADR-0011](0011-fit-is-a-facet-set.md).** Both: the object
   must carry enough structured context for distance to be computed, but the distance itself
   exists only relative to a target, so it is computed and never stored. Exposed as a **facet
   set** — geography, sector, org size, control environment, measurement basis — never a composite
   score, so the analyst decides which mismatches bite. He also warned that calling the artefact a
   *"parameter"* sneaks portability back in after we had just retired it; ADR-0011 accepts that
   too.
2. **Does "what it can't end up supporting" generalise beyond the tail?** ADR-0008 declares it
   for maxima. Whether every parameter owes a statement of what it cannot bear is undecided.
