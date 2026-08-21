# Execution plan — corrections first, then one deep thing a week

*Written 2026-08-21 at the owner's instruction: plan in advance, and fix what is already
inconsistent rather than mutating the project without consistency. Reviewed at each session close.*

## The rule this file exists to enforce

**One big objective a week, occasionally two. Deep, not broad.** A week is the unit because the
last two arcs both showed the same failure: work landed faster than the documents describing it,
and three hand-written numbers, three retired framings and one already-read "biggest blocker" went
stale inside seven days.

**Corrections land before features.** Every item in Part 1 is a place where the repo currently
contradicts itself. Building on top of a contradiction is how the README ended up selling a framing
that had been retired three months earlier.

---

## Part 1 — Backlog corrections (do these first)

Ordered by how much damage each does if left. None is large; together they are about one week.

### C1 · ADR-0006 says depth, the project does breadth

**Accepted 2026-07-31**: *"effort goes to making existing shards more defensible."* Measured since:

| | |
| --- | ---: |
| releases since ADR-0006 | **9** |
| of those showing any parameter movement | **0** |
| `source-backed` across all of them | 66/66, flat |
| commits to `sources/audit.yaml` in the same window | **14** |

The effort went to the audit — breadth of **sources** — and [ADR-0016](../adr/0016-the-audit-is-the-product.md)
blessed that three weeks later without revisiting ADR-0006. **An Accepted ADR is describing a
strategy that stopped.**

**Fix:** amend ADR-0006 to state the axis properly — depth on shards, breadth on sources — with the
measurement above as the reason. Do not silently reverse it; its two surviving arguments (shared
bridged impact, one maintainer's defence capacity) still hold and belong in the amendment.

### C2 · ADR-0007 has been Proposed for two weeks and is now load-bearing

Parts 3 and 4 (which basis mixes are acceptable, and CI gating) were deliberately left open on
2026-08-07. That was fine while nothing depended on it. **It is now the gate on the composition
direction**: assembling anchors across the corpus is exactly how finding 2 gets reproduced at scale.

**Fix:** decide parts 3 and 4, or record explicitly that they stay open and that composition is
therefore restricted to nearest-shard borrowing until they close.

### C3 · ADR-0018's preconditions answer a question that may not exist

They gate rebuilding **a control that returns nothing**: no trap pairs, and a majority of
combinations answering. If the design becomes *always return a number, labelled*, an empty answer
never occurs and those conditions are meaningless rather than met.

**Fix:** scope the preconditions to that control in the ADR text, so a future reader cannot take
them as a blanket bar on reader-supplied targets.

### C4 · ADR-0016 freezes the engine; the next objective is engine work

Part 3: *"the engine, simulation and console are frozen — bug fixes and correctness only."*
Composition is a new engine capability.

**Fix:** decide whether composition counts as correctness (it makes an existing published surface
honest about what is in it) or as a new surface needing an amendment. **Do not build first and
classify afterwards.**

### C5 · The roadmap has no axis for any of this

M1–M5 are audit-shaped. The composition direction is a second axis and would be bolted on as an
afterthought.

**Fix:** rewrite the roadmap around two tracks — **the audit** (M1–M5, unchanged) and **usability**
(the composition work) — with the second gated on C1–C4.

### C6 · `NEXT_STEPS.md` is 1,900 lines and its top section is a graveyard

Reconciled 2026-08-21, but the structural problem remains: the "Pending on the owner" block at the
top accumulates struck items, and the one entry that mattered named an already-read source as the
biggest blocker for six days.

**Fix:** cap the pending block at what is actually owed, and move closed items to a dated archive
section. The restart point is the only part that must be current.

### C7 · Three hand-written numbers went stale in one week

The card's coverage line (twice), ADR-0018's grid counts, and a roadmap figure. All are generated
or tested now.

**Fix:** make it a rule rather than three fixes — **any number appearing in public text is
generated or pinned by a test.** Add it to `AGENTS.md` under the rules that are easy to get wrong.

---

## Part 2 — The weekly sequence

Each week is one objective. Nothing starts until the prior week's is merged, released or explicitly
parked. A week that ends with a document out of date with the code has failed, whatever shipped.

| week | objective | gate |
| --- | --- | --- |
| **W1** (from 2026-08-22) | **The corrections.** C1–C7. Ends with every ADR describing what the project actually does. | none — do it |
| **W2** | **Composition on the 11 shards you already hold.** Not arbitrary cells. Partition each shard's modeled average by evidence class (measured / bridged / interpolated) using the analytic method already in `engine/tail_sensitivity.py`. Deterministic, checkable by hand. | C1, C4 |
| **W3** | **The portable object.** One click gives the composed figure, its breakdown, the cell, and the pinned release — reproducible by a stranger who has neither. Extends the existing "cite this number" interaction; no second step. | W2 |
| **W4** | **Arbitrary cells by nearest-shard borrowing.** Turns 456 empty answers into 456 labelled ones. Borrowing only — bespoke assembly stays shut until C2 closes. | W2, C2, C3 |
| **W5** | **Reader context, client-side.** Revenue and size sharpen selection and scaling. Nothing sent, nothing stored, exactly as the ADR-0014 control worked. | W4 |
| **W6+** | **UI**, then reassess. By here there is something worth looking at, and not before. | W5 |

**Not scheduled, and deliberately:** contributions back to the ledger (piece E). It is the only part
needing a backend, a privacy posture and a breach surface. **It gets decided with usage data or not
at all.**

**Running alongside, not competing:** M1 continues whenever documents arrive — that is reading, not
building. **2026-11-01 is fixed** ([ADR-0017](../adr/0017-the-kill-criterion-gets-a-clock.md)) and
lands mid-sequence; the registry decision is not deferred because the composition work is
interesting.

## Part 3 — What would stop this

Recorded now, while it is cheap to say:

- **If W2's composition numbers are not interpretable on evidence we know cold**, the idea is
  wrong and stops there. That is what W2 is for.
- **If the ADR-0009 amendment cannot be written honestly** — if the only justification is that it
  would be nice to have — it does not get built. The scope gate is the asset.
- **The audit is still the product.** If usability work starts crowding out reading sources, the
  ordering is wrong. The composition direction exists to make the audit *reachable*, not to replace
  it.
