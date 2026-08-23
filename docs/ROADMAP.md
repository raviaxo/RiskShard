# Roadmap

*Rewritten 2026-08-19. The previous roadmap planned new shard families and is archived as
[declined](internal/declined_emergent_risk_scenarios.md) — it failed the
[ADR-0009](adr/0009-what-riskshard-is-and-is-not.md) test. This one has an end. Every milestone
is a number you can check without asking us, and the last one has a date that
[ADR-0017](adr/0017-the-kill-criterion-gets-a-clock.md) already committed to in writing.*

## Two tracks, and only one of them is open-ended

**Track A — the audit.** Reading every public cyber-loss source we cite, one at a time, and
recording what each one actually publishes. Not more sources — *these* sources, finished.
[ADR-0016](adr/0016-the-audit-is-the-product.md) makes it the only growth surface, and M1–M5 below
are unchanged.

**Track B — usability.** Whether a reader can get anything out of what the audit produces. It
exists because of a defect measured here, not because it would be nice: **the corpus answers a
reader who tells it nothing and refuses one who describes themselves**. Track B is deliberately
short, mostly gated, and it does not compete with Track A — if it starts crowding out source
reading, the ordering is wrong.

> **The tracks are not equal.** Track A finishes. Track B has no end state and is therefore capped
> rather than planned: one item at a time, each needing its own decision before it starts. That
> asymmetry is the point — it is what stops a second axis quietly becoming a second project.

---

## Track A · M1 — Finish the audit · **63 of 75** · target 2026-09-15

Every registered source read on all four properties: does it publish a **mode**, a
**distribution**, an **exceedance statement**, and can you **name the population** it measured.

| | |
| --- | ---: |
| sources read on all four properties | **63 of 75** |
| answers verified against a stored artifact | **252 of 300** |
| sources held only as a pointer, needing a person | **12** |
| sources unread but readable | **0** |

**Updated 2026-08-22 — the last readable source was read, and one of the 13 was never blocked.**

- **CSA Singapore Cybersecurity Health Report 2023** was the only row left as `unverified`: an
  image-based PDF whose text extraction returned 791 words of headings. Read by rendering all ten
  pages and reading them. It publishes **no monetary loss figure at all** — business impact is
  reported entirely as the incidence of impact *types* (48% business disruption, 31% financial
  loss), never magnitude — so mode, distribution and exceedance are all *no*, and population is
  *yes* and unusually specific. **The unread category is now empty**: every remaining gap is a
  document nobody holds.
- **The 2025 manufacturing sector report had two audit rows that contradicted each other.** One
  said the report was gated and we held a 1,648-word web page; the other recorded the 7.1 MB PDF
  read on 2026-08-16, from which comes *"extreme demands of $5 million or more — accounting for a
  fifth (20%) of demands"* — the most directly usable exceedance in the corpus. The stale row is
  removed and `audit_defects` now fails on a duplicate `source_id`, which nothing checked. **This
  is the sixth time a source recorded as owed turned out to be held.**

**12 sources are the rest of M1.** Progress on 2026-08-20/21 came from three places at once, and
only one of them was a fetch:

- **The Japan workbook was never unreadable, only unread.** Its 88 sheets resolve fine with a
  library that handles shared strings, and it turns out to publish a **banded cost distribution**
  (n=89) and a **stated exceedance** — 5 of 89 investigations above ¥100M. It had been sitting as
  `unverified` because the first reader returned 461 words and no CJK text.
- **Sophos State of Ransomware 2026 global** arrived and answers all four: no mode, a banded
  payment distribution, an exceedance at USD 1M, and a named population of n=2,158.
- **Two Singapore Cyber Landscape editions** registered, which supersede the CSA Health Report
  2023 the corpus had been stuck on.

**Four of the seven documents supplied were already held** — the same lesson as the v0.9.0 arc.
Before hunting for a source, check what the corpus thinks it has.

What remains needs a person: IBM regional cuts, AFP (**declined 2026-08-21**), CESIN, MYOB, and
the older Sophos sector cuts. **Cyentia IRIS was already fully read** — an earlier version of this
list said otherwise and was wrong.

**Done means:** `riskshard_doctor.py` prints 72 of 72, and the phrase *"the audit is complete"*
becomes true and publishable. It is a headline exactly once.

## Track A · M2 — Publish the audit as its own artifact · ✅ **done 2026-08-19**, ahead of target

[**raviaxo.github.io/RiskShard/audit.html**](https://raviaxo.github.io/RiskShard/audit.html)

All 72 registered sources, four questions each. Every answer states what it was checked against,
carries the document's SHA-256 and the date it was read, and can be disputed from its own row.

The four-questions table is the finding in one place, counted against what has actually been read:

| property | publishes | of sources read |
| --- | ---: | ---: |
| mode | **0** | 58 |
| distribution | 12 | 58 |
| exceedance | 17 | 58 |
| population | 45 | 58 |

Built by `scripts/build_audit_page.py` from `sources/audit.yaml` and deployed with the explorer.
Nothing on it is hand-written. Nine tests pin the things a table quietly gets wrong: a count
without its denominator, an unread source rendered as a source that publishes nothing, and a
blocked answer rendered as a backlog item.

## Track A · M3 — Make it possible to join in · **started 2026-08-20**

The four questions, in words someone who has never met this project can answer, and a route to
answer them in. [ADR-0016](adr/0016-the-audit-is-the-product.md) decided the ask a week ago — *read
one source, answer four questions, twenty minutes* — and nobody had been given a way to do it.

**Why this comes before the spec, and it is a correction to how this milestone was first written.**
The obvious reading of zero contributors is zero demand, and that reading is wrong. The questions
existed only in beta-PERT vocabulary, the front door ran one piece of jargon every 25 words, and
there was no form to answer anything in. **Nobody declined; nobody could tell what was being
asked.** A spec written before that is fixed is a second unread document, which is the way
[ADR-0012](adr/0012-loss-event-registry-bounded-trial.md)'s registry trial already failed once.

Shipped so far:

- **The four questions in plain words**, leading on every surface, with the precise wording kept
  underneath because that is what makes two people's answers comparable.
- **A form that is the four questions and nothing else**
  ([`read_a_source.md`](https://github.com/raviaxo/RiskShard/issues/new?template=read_a_source.md)),
  which says out loud that *"I could not tell"* is a real answer and that a question may be badly
  framed.
- **A name for the job**, because it has no category and a reader needs somewhere to file it:
  *cyber loss figures get quoted far past what they can support, and nobody checks.*

**Still to do:** ask three named people directly. A route nobody is pointed at is the same as no
route, and that is the mistake this milestone exists to not repeat.

**Done means:** one person outside the project produces one audit row. Then the spec gets written
from what confused them, rather than from what we imagine would.

## Track A · M3b — Amount shape and treatment · **blocked, and split out 2026-08-20**

Split from M3 because it is a different specification of a different object: the four questions
audit **sources**, this labels **loss records**. Bundling them made the whole milestone wait on one
question with no route to its author.

Blocked on the `recovery` question for John Flack — does an insurance recovery stay a distinct
quantity, or become a treatment of one? Background:
[`amount_shape_design_input.md`](internal/amount_shape_design_input.md). GRC EC publishing is
paused; talking there is not, so this is a direct message rather than a post.

## Track A · M4 — The registry decision · **2026-11-01, fixed**

[ADR-0017](adr/0017-the-kill-criterion-gets-a-clock.md) pre-committed this date and states in
writing that **it does not move again**. At the first release on or after 2026-11-01, count:

1. shards whose `impact.max` cites a registry entry — **0 today**
2. entries contributed by anyone outside the project — **0 today**

If neither has moved, the registry retires. **No external readership at the date is not grounds
for another extension** — it is grounds for retiring it and publishing that the trial never got a
fair test. The doctor prints the date on every run.

## Track A · M5 — The adoption test · measured at M4

Whether any of this is used, stated as numbers rather than impressions:

- has anyone **cited** a parameter or the audit?
- has anyone **disputed** a row?
- has anyone **applied the standard** to a source we did not read?

All three read zero today. Published either way.

---

## Track B · U1 — Say what each published figure rests on · ✅ **done 2026-08-22**

Every shard is partly bridged and the page does not say by how much. The corpus total is published
(**7 of 66** parameters drawn from the population they are used for) but the per-shard split is
not, and it is concentrated rather than spread: **four shards hold all seven and seven hold none.**
No shard is complete on the cell it is named after.

The page publishes each parameter's bridge flag, and — for impact only, and only above 50% — the
maximum's share of the figure. **Nothing joins the two.** So a reader cannot learn how much of a
figure rests on anchors measured somewhere other than their cell, and the frequency side carries no
weighting at all. That join is [finding 10](FINDINGS.md): no shard is well anchored on both
families, and the strong sides never coincide.
[ADR-0016 part 3](adr/0016-the-audit-is-the-product.md) classifies correcting it as correctness, on
the narrow ground that a published count misdescribing the figure beside it is an inaccuracy in
something already shipped rather than a new surface.

**Done:** each of the eleven items states its own composition, per family and never blended, and
tests fail if the payload goes null, if the template stops reading it, or if it fails to serialise
into the page.

**And it travels.** Every anchor has had a `[cite]` since v0.4.0; the modeled average never did, so
the one number most likely to reach a slide was the only one that copied bare. `[cite figure]`
emits the figure with what it rests on, pinned to the release — and returns nothing at all when the
composition is missing, so there is no code path that copies the number alone. That is
`composition_direction.md`'s second decision (the unbacked portion is stated, never blended) applied
to the copy path, which is where a screenshot's honesty is actually decided.

**Deliberately not built:** an `RS:cell(...)` identifier and resolver. A cell identifier earns its
keep only when a reader can name a cell we have never published, which is **U2** and is gated. For
the eleven we do publish, the shard id plus the pinned release already identifies the figure and
`citeURL` already pins it.

## Track B · U2 — An answer for a cell we have never published · **gated, not scheduled**

Turning 456 dead ends into labelled answers. **Not started, and it cannot start on this roadmap
entry** — it is a new surface, not correctness, and three things gate it:

1. **An ADR that does not exist.** [ADR-0009](adr/0009-what-riskshard-is-and-is-not.md) declines a
   new axis unless it answers a defect measured in our own data. The specificity inversion is such a
   defect, so the amendment is available — but it has to be written and accepted, not assumed.
2. **Its own failure condition, stated first.**
   [ADR-0018's amendment](adr/0018-the-target-selector-failed-measurement.md) requires it: this
   project already shipped one reader-facing feature decided on what it *could* compute rather than
   on what its answers would say. At least **84.6%** of composed answers would be built entirely
   from anchors measured elsewhere, and a feature whose commonest output is *"this is entirely
   borrowed"* has not obviously improved on one whose commonest output is *"nothing here"*.
3. **Borrowing only.** [ADR-0007's standing restriction](adr/0007-construct-coherence.md) permits
   inheriting a shard's anchor set whole and forbids assembling a bespoke one across the corpus.
   **Re-grounded 2026-08-23** when ADR-0007 was Accepted: the blocker is no longer an undecided
   policy but a missing instrument — the closure requires a composed range to declare what it is,
   and `module_coherence` runs per shard, so a composed cell is the one range that cannot be
   labelled. **This lifts on a build, not on a decision.**

**Recorded so nobody has to reconstruct it:** the design input is in
[`composition_direction.md`](internal/composition_direction.md), and the owner's two decisions
there — a breakdown never a grade, and the unbacked portion stated never blended — stand.

## What this roadmap declines

Recorded rather than left implicit, because every one of these is a good idea and good ideas are
how this project loses focus. [ADR-0009](adr/0009-what-riskshard-is-and-is-not.md): *a new declared
axis may only be born from a defect measured in our own data, never from a good idea about
measurement.*

- **More shards, countries, or threat families.** Coverage is not the constraint; the audit is.
- **New emergent scenario families** — AI-as-liability, systemic loss, regulatory loss.
  [Archived here](internal/declined_emergent_risk_scenarios.md) with the reasoning intact.
- **A better engine, or engine features.** It exists to expose defects in the anchors, and it does
  that already. [ADR-0016 part 3](adr/0016-the-audit-is-the-product.md) freezes it to bug fixes and
  correctness; its 2026-08-22 amendment draws the line at the **published cell** — repairing a
  disclosure the page already attempts is correctness, producing a figure for a cell we have never
  published is not.
- **A CRQ methodology.** ADR-0009 settled it.
- **Bringing back the reader-target selector.** [ADR-0018](adr/0018-the-target-selector-failed-measurement.md)
  retired it on a measurement and set two conditions for reconsidering, **both still false**: no two
  facet values may each answer alone and answer nothing together (60 pairs do), and a majority of
  targets must answer something (83 of 539 do, which is 15%). Neither moved in this arc.

  **The 2026-08-22 amendment scopes those two conditions to that control** — a selector whose answer
  can be empty — rather than to reader-supplied targets in general. A design that never returns
  nothing does not satisfy them (borrowing an anchor does not make a parameter measured on the
  reader's cell) and does not inherit them either; it owes its own failure condition instead, which
  is what gates U2 above. **Coverage still has to move for the selector, and coverage is not what
  this roadmap is buying.**
