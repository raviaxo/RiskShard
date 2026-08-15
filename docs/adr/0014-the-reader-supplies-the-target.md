# ADR-0014 — The reader supplies the target

- **Status:** Accepted (2026-08-15)
- **Date:** 2026-08-15
- **Deciders:** repo owner
- **Closes:** [ADR-0011](0011-fit-is-a-facet-set.md) open question 1
- **Related:** [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md) (the portability
  claim this must not re-import), [`0011-fit-is-a-facet-set.md`](0011-fit-is-a-facet-set.md)
  (fit is a facet set against a stated target; **no composite score, ever**),
  [`0013-fit-is-derived-not-stored.md`](0013-fit-is-derived-not-stored.md) (which made this
  possible), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope gate)

## Context

[ADR-0011](0011-fit-is-a-facet-set.md) decided that fit is computed against a **stated target** and
that computing it against our own shard cell is *"a convenience for one consumer — us."* It listed,
as an open question, whether a consumer-supplied target should become a first-class artefact, and
left it unscheduled.

[ADR-0013](0013-fit-is-derived-not-stored.md) then retired the stored field, making fit a pure
function of `(declaration, target)`. Its Decision part 1 noted the consequence:

> *"Compute fit against my cell" stops being a future feature requiring re-authoring of 141 records
> and becomes a matter of passing a different target.*

**Checking what the published page already carries turns that from cheap to nearly free.** The
explorer's data payload includes `declared_for` on every parameter — the measured population, facet
by facet — because ADR-0011 promoted it to a reader-facing field. The reader's browser therefore
already holds every input the derivation needs. Nothing has to be fetched, stored, authored or
added to the schema; the rule is roughly fifteen lines of the same comparison the engine makes.

So the question is no longer *what would it cost* but *does it re-import the claim we retired*.

## The risk this decision exists to bound

[ADR-0010](0010-where-riskshard-stops.md) retired "Metasploit for risk" because its load-bearing
claim was **portability**: take the module, know your target conditions, run it. A feature that
asks a reader for their cell and then answers is one small step from telling them which parameters
are *good for them*, which is portability with a nicer interface.

The distinction that keeps this honest is narrow and worth stating plainly:

- **Distance is ours to compute.** Whether a source's declared population names your country, your
  sector, your size band, your threat is a fact about two declarations. We can compute it, and we
  should, because we already compute it for ourselves and it is unhelpful to make every reader do
  by hand what we do by machine.
- **Whether that distance disqualifies the number is not ours to compute.** A geography mismatch is
  fatal to one analysis and irrelevant to the next. Only the reader knows which.

The feature must answer the first and refuse the second.

## Decision

**A reader may supply their own cell, and every fit line recomputes against it. The result names
the target it was computed against, states mismatches facet by facet, and never scores, ranks,
recommends or persists anything.**

Six parts.

### 1. The reader's target is an input, not a stored artefact

It lives in the page for the length of a visit. No account, no profile, no submission, no
server-side record, and no `org_profiles/` entry — that gap remains measured, elevated and
unscheduled, and this ADR does not license filling it.

The answer to ADR-0011 open question 1 is therefore **"a first-class *input*, not a first-class
*artefact*."** A target is something a reader has, not something this project curates.

### 2. Exactly one rule, and it is the engine's

Fit against a reader's cell is computed by the same strict rule ADR-0013 adopted: **bridged on a
facet when the declared population does not name that facet's value for the target.** No wildcard
exemption, no separate consumer-friendly variant, no rounding of the caveat. If a reader's number
differs from ours it is because their cell differs, never because the rule did.

A facet the reader leaves unset is **not tested** rather than assumed to match, which is the
engine's existing behaviour for a cell with no value on that facet.

### 3. The refusals, carried over intact

No composite fit score, grade, percentage or star rating for a parameter, a shard, or the
portfolio — [ADR-0011](0011-fit-is-a-facet-set.md) Decision part 2, restated here because a target
selector is exactly where a reader would expect one and exactly where it would do the most damage.

Also refused, as the same claim wearing different clothes: **no sorting or ranking of shards or
parameters by fit**, and **no recommendation** — nothing that says a parameter is suitable,
usable, or "a good match" for the supplied cell. Ordering the page by fit would assert the
commensurability that a scalar asserts, just spatially.

### 4. What the reader gets is the mismatch, stated

For each parameter: the facets on which the declared population does not name their cell's value,
named individually, with the target named beside them. That is the whole answer. What it means for
their analysis is their call, and the page says so.

### 5. Our cell stays the default and stays labelled

The page opens computed against the shard's own cell, exactly as before, and the published
portfolio counts continue to describe *that* — they are the release's numbers, cited in the data
pack and pinned by tests. A reader's target changes what their screen shows, never what the release
published. Any count shown against a reader's cell is marked as theirs and is never presented as
the project's figure.

### 6. It must degrade to today's behaviour

With no target supplied, the page is byte-equivalent in meaning to the current one. This is a
layer over the existing render, not a replacement for it.

## Scope gate

[ADR-0009](0009-what-riskshard-is-and-is-not.md) asks: does this make an existing published number
more correct, or the method more sophisticated?

**Neither, strictly — and that is worth being honest about rather than arguing around.** It adds no
axis, no data, no methodology and no measurement; it changes no published figure. What it does is
make an already-published fact *legible to the person it concerns*: we compute distance against our
cell and print it, while the reader's cell is the one that decides anything, and until now they had
to do that comparison by eye across 66 rows.

It clears the gate on the ground that ADR-0011 named this the correct shape of the artefact — *"the
evidence object's duty is to carry enough structured context that any consumer can compute distance
against their target"* — and this is the last step of that duty, not a new ambition. **If the
feature ever starts answering *whether* a number suits a reader, it has left this justification and
violates ADR-0010.**

## Consequences

- **The project can be used, not only read.** A visitor can ask a question about their own context
  and get an answer grounded in declarations rather than a pitch.
- **Our own headline stops looking like a verdict on the corpus.** 7 of 66 is *our* cell's number;
  a reader whose cell is `US · all · all · data_breach` will see a very different one, and both are
  the same evidence. That is the clearest possible demonstration of the ADR-0010 thesis, and the
  page will now demonstrate it instead of asserting it.
- **A new drift surface.** Every future addition to this control must be checked against part 3.
  The natural next asks — "sort by best fit", "show me only what matches", "score my coverage" —
  are all refused by this ADR, and refusing them is the maintenance burden it creates.
- **`applicability` becomes load-bearing for readers, not just for us.** A sloppy declaration now
  produces a wrong answer on someone else's screen. Finding 5's detector and finding 6's derivation
  both get more important, not less.

## Alternatives considered

- **Leave it to the analyst entirely** — publish `declared_for` and stop. Rejected on ADR-0011's
  own reasoning: the raw material being present is not the same as the comparison being feasible,
  and asking a reader to do 66 four-facet comparisons by eye is how a caveat gets skipped.
- **A server-side target profile / saved cells.** Rejected as part 1: it makes a reader's context
  into our artefact, invites an account, and is a product decision this project has not earned and
  does not need.
- **Show a "fits your cell" count as the page headline.** Rejected under part 5 — it would replace a
  released, citable figure with a per-visitor one and quietly make the reader's number *the*
  number.
- **Sort parameters or shards by fit.** Rejected under part 3. It is a fit score expressed as
  position, and it would be the single easiest way to undo ADR-0011 part 2 without appearing to.
- **Ship it without an ADR** — it changes no schema and no published number. Rejected: the risk here
  is not technical, and the refusals in part 3 are the entire substance. An unrecorded refusal is
  one a future contributor will implement in good faith.

## Open questions

1. **Does a reader's cell deserve to be shareable?** A URL carrying a target would let one
   practitioner send another "here is how this evidence sits against our context," which is the
   conversation this project wants to be in. It also creates a link that asserts a fit result
   outside the page's own framing. Not decided here.
2. **ADR-0011 open question 2 stays open** — whether the observation period a measurement covers
   deserves promotion to a fit facet. It would be a fifth facet in this control if it ever lands.
