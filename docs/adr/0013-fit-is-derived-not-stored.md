# ADR-0013 — Fit is derived against a target, not stored on the record

- **Status:** Accepted (2026-08-15)
- **Date:** 2026-08-15
- **Deciders:** repo owner
- **Closes:** [ADR-0011](0011-fit-is-a-facet-set.md) open question 3
- **Related:** [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md) (`population_match`,
  and the dilution-vs-borrowing distinction this ADR retires from the stored layer),
  [`0011-fit-is-a-facet-set.md`](0011-fit-is-a-facet-set.md) (Decision part 1, which this
  implements), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope gate)
- **Measurement behind it:** [finding 6](../FINDINGS.md), derived by
  `engine/provenance.py` → `derivable_bridges()`

## Context

[ADR-0011](0011-fit-is-a-facet-set.md) decided that fit is computed against a stated target,
exposed as a facet set, and never presented as a property of the evidence object alone. Its
Correction section then recorded that the repository does not do this: `population_match.bridged_on`
is computed against the authoring shard's cell and **frozen onto the record**, which Decision part 1
forbids.

It left three options open — store the target alongside the fit, compute fit per consumer, or
relabel the field as an authored judgement about our own cell — and declined to choose, on a stated
premise:

> It cannot simply be derived away. An `all` declaration is deliberately *dilution* rather than
> *borrowing* under ADR-0003 — an all-sector average includes our sector, where a UK-only measure
> genuinely excludes the US — and only the author can make that call. Deriving the field
> mechanically loses that judgement: a naive derivation flags 45 of 66 cards as bridged against the
> 35 recorded, precisely by collapsing dilution into borrowing.

**That premise was not measured when it was written. It has now been, and it does not hold** — not
because the distinction is unreal, but because the repository is not making it.

## What the measurement found

Published in full as [finding 6](../FINDINGS.md). Three results decide this ADR.

**The stored field disagrees with its own declarations on two cards in three.** Stored fit equals
derivable fit on **21 of 66** cards. Counted as individual facet claims, the repository stores
**43** and the declarations support **117**.

**The disagreement is one-directional and concentrated in one declaration.** No card claims a
bridge its declaration does not support — finding 5's guarantee, holding at 0 of 66. The entire gap
is bridges the declarations support and the records do not claim, and almost all of it is
`[all]`: across the corpus a wildcard declaration fails to name our cell's value **100** times, and
is **recorded as a bridge 28 times and left unrecorded 72 times.**

**The same call goes both ways inside a single file.** `evidence/au_finance_bec.yaml` holds
`accc_abs_au_small_business_scam_loss_report_rate_floor_2025` (declares `industries: [all]`,
`company_size_bands: [all]` → stores `matched`) and
`abs_2025_au_business_cyber_incident_prevalence_frequency_likely` (declares the same two fields the
same way → stores `bridged_on: [sector, size, threat]`). Both records' `limitations` state the
mismatch in prose.

So the judgement ADR-0011 protected is not a judgement in the data. It is drift — the same class of
drift finding 5 repaired one field over, where prose said *borrowed* and the structured field said
*matched*.

### The alternative derivation was measured too, and it is quieter

The obvious way to preserve the dilution/borrowing distinction mechanically is a
**containment-aware** rule: a wildcard population *contains* our cell, so it dilutes rather than
borrows; a named set that omits our value *excludes* our cell, so it borrows. It is a coherent
rule, and it was measured against the corpus.

| | stored today | strict (declaration does not name our value) | containment-aware |
| --- | --- | --- | --- |
| cards carrying at least one bridge | 35 of 66 | **59 of 66** | 7 of 66 |
| individual facet claims | 43 | **117** | 7 |

The containment-aware rule publishes **7 facet claims against the 43 the repository publishes
today**. Nearly every declaration in the corpus is a wildcard on at least one facet, so a rule that
exempts wildcards erases most of the caveat — including **10 of the 15 country bridges**, because a
global survey declares `countries: [global]`. It would make the front door quieter, which is the
one direction `AGENTS.md` does not allow a caveat to move.

**The strict rule is also already in the repository.** `_card_population`'s country layer has always
computed country strictly, against the shard's country, at read time, with no wildcard exemption —
which is exactly why country is the single facet where stored and derived agree at 15. The stored
layer and the country layer have been running two different definitions of the same field.

## Decision

**`population_match` stops being an authored field and becomes a value computed against a named
target. The strict rule is the derivation: a record is bridged on a facet when its declared
population does not name that facet's value for the target being computed against.**

Four parts.

### 1. Derived, not stored

Fit is a pure function of (declaration, target). Nothing is read from a stored `population_match`
when rendering fit. This is [ADR-0011](0011-fit-is-a-facet-set.md) Decision part 1 made structural
rather than conventional: a value that is computed cannot be frozen against the wrong target,
because there is no place to freeze it.

The consequence ADR-0011 wanted follows for free. *"Compute fit against my cell"* stops being a
future feature requiring re-authoring of 141 records and becomes a matter of passing a different
target.

### 2. Dilution is carried by the caveat, not by the fit

The distinction between an all-sector average that includes us and a UK-only measure that excludes
us is **real and is not encoded in this field**. It is carried where it has always actually been
carried: in `limitations`, in prose, per record, which is where both AU BEC records above stated it.

This is a deliberate loss of resolution in the structured layer, and it is recorded as one. The
alternative was measured and publishes a third of the caveat the repository publishes today.

**It also retires ADR-0003's "matched by method" exemption, and that exemption was not drift.**
[ADR-0003](0003-shared-impact-bridges.md)'s implementation decisions hold that same-survey
adjacent-band anchors, documented single-case anchors and statutory parameters are *the
range-anchoring method, not borrowing*, and therefore matched. That is a defensible rule, applied
deliberately. Strict derivation does not honour it: **5 of the 24 cards that flip from matched to
bridged are exemptions of exactly this kind** — two statutory penalty caps (`privacy_act_1988`,
`gdpr_article_83`), one documented single-event anchor (`afp_2020_au_bec`), and the two same-survey
adjacent-band anchors in the FR shard, where a small-business and a large-business band of one
French survey bracket a mid-market cell.

The rule is kept and moved. A statutory cap is not a measurement of anyone's population, and
saying so is a *stronger* caveat than calling it matched — but the place to say it is
`measurement_basis` ([ADR-0007](0007-construct-coherence.md)), which already distinguishes
`statutory_penalty_cap` and `single_documented_event_loss` from measured statistics, and which no
reader has to infer from a fit facet. Losing the exemption costs precision on 5 cards and buys a
field that means one thing.

### 3. The stored field is retired from the schema, not left to rot

`population_match` is removed from `schemas/evidence_record_schema.json` and from the 141 records,
rather than being left in place and ignored. A field that no longer drives what is rendered but is
still accepted by the schema is a trap for the next contributor, who will author it carefully and
change nothing.

Removal is safe to assert and must still be proven at implementation: the field is read only by
`engine/provenance.py` and `scripts/explorer_template.html`, and by nothing in calibration,
coherence, exceedance, readiness or the simulation.

### 4. The counts move louder, and the move is published

Deriving strictly changes two published counts: cards drawn from the shard's own cell
**31 → 7 of 66**, and bridged cards **35 → 59 of 66**. Cards bridged across country stay at **15**.
No loss figure, distribution, portfolio total or shard AVG/P95/P99 moves.

**"Half our parameters are borrowed" becomes "seven of sixty-six are not."** That is the honest
statement of what this corpus is, it is a harder thing to publish than the current number, and it
ships as a correction on [`FINDINGS.md`](../FINDINGS.md) rather than as a quiet recount.

## Scope gate

[ADR-0009](0009-what-riskshard-is-and-is-not.md) asks: does this make an existing published number
more correct, or the method more sophisticated?

**More correct.** It introduces no measurement axis, no new field, no new data, and no methodology.
It removes a field and computes what it used to assert. The defect it answers was measured in our
own data, which is the only origin ADR-0009 permits for this kind of change.

## Consequences

- **A published count gets worse in public.** 31 of 66 cell-matched was the strongest number on the
  provenance surface and it was resting on an inconsistently maintained field.
- **Contributors lose an authoring decision.** Declaring `applicability` honestly is now the whole
  job; fit follows from it. Given that the decision was being made two ways for the same input, this
  is a reduction in the number of ways to be wrong.
- **Five cards lose a distinction they had honestly earned.** The statutory caps, the documented
  single-event anchor and the two adjacent-band anchors named in Decision part 2 will read as
  bridged on sector and size. Their `measurement_basis` already says what they are; a reader who
  stops at the fit facet will now see a caveat that is louder than the record deserves. That is the
  price of the field meaning one thing, and it is stated here rather than discovered later.
- **`unexplained_bridges()` becomes vacuous and its finding becomes history.** Stored bridges are
  what it checks; with none stored, finding 5's detector has nothing to detect. It is kept as a
  contributor-facing check against the *declaration* shape and finding 5 stays on the page as a
  record of what was repaired.
- **ADR-0003's `population_match` is superseded in part.** Its bridge *vocabulary* (country ·
  sector · size · threat) survives unchanged and is what the derivation emits; its stored-field
  mechanism does not.
- **The explorer and evidence report change what they show, not what they claim.** Both already name
  the target wherever fit is rendered ([#136](https://github.com/raviaxo/RiskShard/pull/136)), so
  the labels are already correct for a derived value.
- **This ADR is itself the fourth correction in eight days.** ADR-0011 recorded a premise about its
  own data that measurement did not support, and the correction is published rather than absorbed.

## Alternatives considered

- **Store the target alongside the fit** (`computed_for`). Rejected: it makes an inconsistent value
  auditable rather than correct, and it leaves the consumer-supplied-target case needing 141 records
  re-authored.
- **Relabel it as an authored judgement about our own cell.** Rejected on the measurement — it
  defends as judgement a call that goes both ways for identical declarations in the same file.
- **Derive it containment-aware.** Rejected on the measurement above: 7 facet claims against 43
  published today, erasing 10 of 15 country bridges. Quieter is the disallowed direction.
- **Repair the 45 cards by hand and keep the field.** This is what finding 5 did for
  `applicability`, so it deserves an answer rather than a dismissal. Rejected because it fixes the
  values without fixing the shape: the field would still be a target-relative value frozen at
  authoring time, ADR-0011 Decision part 1 would still be violated, and the next contributor would
  still face the same two-way call with no rule to apply.
- **Do nothing until a consumer asks for their own target.** Rejected: the field is published now
  and wrong now.

## Open questions

1. **Does `applicability` need a vocabulary for "measured over a population containing ours"?**
   Decision part 2 pushes dilution into prose. If a structured form is ever wanted, it belongs on
   the declaration (what was measured) and not on the fit (what it is far from) — but no source
   publishes it in a form that would fill such a field, and inventing one is out of scope under
   ADR-0009.
2. **ADR-0011 open questions 1 and 2 stay open.** Whether a consumer-supplied target becomes a
   first-class artefact, and whether the observation period deserves promotion to a fit facet, are
   untouched here.
