# The composition direction — captured 2026-08-21, not yet decided

*Owner's design input from the 2026-08-21 discussion, recorded before it lives only in a chat
window. **Nothing here is accepted.** It collides with four ADRs and needs its own before code
moves — see [`execution_plan.md`](execution_plan.md) for the corrections that come first.*

## What was proposed

**Never return a dead end.** Whatever cell a reader names — geography, size, sector, threat — they
get a number. If it is anchored to sources, say so. If it is not, they still get one, with the
context stated, run through the same simulation.

**The audit becomes the lever, not the gate.** Today the audit decides what we will publish. In
this direction it decides what a number is *labelled as*, and the number is always produced.

**More context from the reader makes it sharper.** Revenue, market cap, EBITDA — cheap for them to
supply, and the more they give the more specific the answer, without us storing anything.

**The output travels.** A file they can take to their leadership: *this is our context, checked
against these sources, after these simulations and calibrations.*

**And it compounds.** More use produces more context, new reports get linked and recalibrated
against, and the thing improves by being used.

## Two decisions the owner made in the discussion

**1. Breakdown, never a grade.** The composition is stated as separate shares — *40% measured on
this cell, 45% bridged, 15% interpolated* — not compressed into a score or a letter.
[ADR-0011](../adr/0011-fit-is-a-facet-set.md) refused a composite twice, because a geography
mismatch is fatal to one analysis and irrelevant to the next. A breakdown keeps the facets
separate and does not reopen that.

**2. The unbacked portion is stated, never blended.** It is reported beside the number, not folded
into it. The headline figure is the **defensible** portion, and the interpolated extension has to
be picked up deliberately. A screenshot of the headline stays honest, which matters because people
screenshot.

**The requirement behind both:** *"they can take it with them easily, and see where the number is
coming from and what it is backed up by."*

## The hard problem that requirement creates, and the answer

A parameter is citable because it lives in a release. **A composed number for an arbitrary cell
lives in no release** — it is assembled in the reader's browser for a cell nobody anticipated. So
there is nothing for a challenger to resolve to, and the whole design fails at the first *"where is
this from?"*

**It does not need to be stored. It needs to be re-derivable by a stranger.**
[ADR-0002](../adr/0002-portable-scenario-seed.md) already made the engine machine-independent, so a
composed figure pinned to a data-pack release plus a stated cell cannot come out different on
someone else's machine. What the reader carries is not a number, it is a recipe that yields the
number:

```
RS:cell(country=AU, sector=manufacturing, size=mid_market, threat=ransomware)
   @2026.08.21-v0.10.0
```

**Backed up because it is reproducible, not because we kept a copy.** That is a stronger guarantee
than a vendor PDF, and it is a property already paid for.

## What it collides with

| | |
| --- | --- |
| [ADR-0009](../adr/0009-what-riskshard-is-and-is-not.md) | Scope gate. This makes a surface more *useful*, not a published number more *correct* — the second category, which ADR-0009 declines. **Needs an explicit amendment, not drift.** |
| [ADR-0010](../adr/0010-where-riskshard-stops.md) | The evidence object is the product and quantification is the reader's step. Always returning a number moves that line. |
| [ADR-0016](../adr/0016-the-audit-is-the-product.md) part 3 | The engine is **frozen** — bug fixes and correctness only. Composition is engine work. |
| [ADR-0018](../adr/0018-the-target-selector-failed-measurement.md) | Its preconditions gate rebuilding *a control that returns nothing*. If a number always comes back, those preconditions are answering a question that no longer exists. |
| [ADR-0007](../adr/0007-construct-coherence.md) | Still **Proposed**. Load-bearing here: assembling anchors across the corpus is exactly how a Frankenstein range gets built, which is [finding 2](../FINDINGS.md). |

**The owner's resolution of the CRQ objection, and it holds:** *"we do not need to own it, just use
it and add value."* ADR-0009 declines becoming a CRQ **methodology project**. Using beta-PERT and
Monte Carlo as commodity components while the product is the labelling is not owning the method.
**Do not invent method. Invent the label.**

## The architecture finding

**Only one piece needs a backend.**

| piece | backend | note |
| --- | --- | --- |
| A · never a dead end | no | |
| B · composition label | no | the differentiator |
| C · more sources | no | shrinks the interpolated share |
| D · reader context (revenue, EBITDA) | **no** | client-side, exactly as the ADR-0014 control worked |
| E · contributions back to the ledger | **yes** | the flywheel, and the only paid-for part |
| F · recalibrate on new reports | no | |
| G · UI | no | |
| H · leadership artifact | no | generated client-side |

The browser payload **already carries** everything a composition needs: `value`, `declared_for`,
`population`, `basis`, `confidence`, `source_name`, `quote`, `caveat`, `exceedance`, plus
shard-level `leverage`. Nothing new has to be fetched or served.

So everything that makes this *usable* costs nothing, and the "nothing is sent anywhere, nothing is
stored" promise on the audit page stays literally true. **Only the network effect costs a company** —
and that decision can be made later, with usage data instead of a guess.

## The open question, and it decides the size of the build

**When a reader names a cell with no shard, where do the anchors come from?**

- **Nearest-shard borrowing** — take an existing shard's anchors and mark what was borrowed. Cheap,
  legible, and the composition explains itself.
- **Best-anchor-per-parameter across the corpus** — assemble a bespoke set. Better numbers, and it
  can silently build a range whose min, likely and max each measure a different quantity over
  different populations. That is finding 2 reproduced deliberately, at scale, which is why
  **ADR-0007 has to be resolved before this option is available.**

Recommendation: start with borrowing.

## Why this is worth taking seriously

Two owner observations that corrected the analysis rather than losing to it, both recorded because
the same error was made twice:

**"The network is zero because we are barely usable."** Zero adoption had been read as evidence
about demand. It is at least as good as evidence about usability, and the same inversion was true
of the contribution problem a day earlier — nobody declined, nobody could tell what was being asked.

**It answers a defect measured here, not a good idea from outside.** [ADR-0018](../adr/0018-the-target-selector-failed-measurement.md)
measured **456 of 539 nameable cells returning nothing**. That is the defect. This is a response to
it, which is the only kind of new axis [ADR-0009](../adr/0009-what-riskshard-is-and-is-not.md)
permits.
