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

## Part 1 — Backlog corrections ✅ ALL SEVEN DONE 2026-08-22

*Kept in full below rather than struck, because three of the seven premises were wrong and the
record of how they were wrong is the useful part. Where a heading and the amendment disagree, the
**amendment** is right — this file was written from memory of the ADRs, and the ADRs were not
re-read first.*

| | premise | outcome |
| --- | --- | --- |
| **C1** | ADR-0006 describes a strategy that stopped | **wrong** — ADR-0016 part 2 says it *honours* ADR-0006. Amended for the two real defects: a stale *Revisit when*, and depth chosen with no live measure (`params_source_backed` was saturated at 66/66 a week before the ADR was accepted). Adopted cell-matched as the measure, explicitly **not** as a target. |
| **C2** | parts 3 and 4 are load-bearing and open | **held** — recorded as staying open, with composed answers restricted to nearest-shard borrowing. The reason is stronger than the plan's: all 11 shards already carry a mixed family and no impact family is coherent, so assembly compounds a universal defect rather than risking a new one. Open question 1 is now on the owner's list. |
| **C3** | ADR-0018's preconditions may answer a question that stops existing | **held, plus a guard** — scoped to that control, **and** stated that composition does not satisfy them by redefining what an answer is. A design with no dead end owes its own failure condition instead: at least 84.6% of composed answers would be wholly borrowed. |
| **C4** | composition is engine work under a freeze | **reclassified** — correctness, not an amendment. The measurement first offered for it was wrong (a "dead render path" that does not exist; withdrawn in ADR-0016), and the classification was re-argued on finding 10: the published count treats an anchor carrying 0.1% of a figure and one carrying 89.1% as equals, so the number beside it is misdescribed. Boundary drawn at the **published cell**. |
| **C5** | the roadmap has no axis for this | **held** — two tracks, Track A (audit, M1–M5 unchanged) and Track B (U1 in flight, U2 gated). Two "declines" bullets contradicted the new amendments and were reconciled. |
| **C6** | NEXT_STEPS is 1,900 lines with a graveyard on top | **held** — 1,995 → 370 lines. Dated narrative and session entries before 2026-08-14 moved to `archive/next_steps_2026-07-to-08.md`; the pending block rebuilt as the single list of what is owed. |
| **C7** | three hand-written numbers went stale in a week | **held, and obeyed in the same commit** — the rule is in `AGENTS.md`, and every figure written into the four documents this arc is pinned by `tests/test_cell_coverage.py`. |

---

### The original entries, unedited



Ordered by how much damage each does if left. None is large; together they are about one week.

### C1 · ADR-0006 says depth, the project does breadth

**Accepted 2026-07-31**: *"effort goes to making existing shards more defensible."* Measured since:

| | |
| --- | ---: |
| releases since ADR-0006 | **9** |
| of those showing any parameter movement | **0** |
| `source-backed` across all of them | 66/66, flat |
| commits to `sources/audit.yaml` in the same window | **14** *(as of 2026-08-21; 15 by 2026-08-22)* |

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

## Part 2 — The weekly sequence, re-cut 2026-08-23

*The original sequence is kept below the line, because how it failed is the useful part. **W1, W2
and most of W3 all landed on 2026-08-22**, in one arc, against a plan that allowed them three
weeks.*

### What the compression actually cost

The pacing rule — *one big objective a week, deep not broad* — was written on 2026-08-21 to stop
work landing faster than the documents describing it. **On that test the arc passed**: most of the
work *was* documents, and every figure written into a public file is now generated or pinned.

**On accuracy it did not.** Five claims made during the arc did not survive being checked, including
a fabricated "dead render path" that reached four documents and two commit messages, and a README
banner that went stale within an hour of the count it quoted moving. Every one was caught by opening
a file; none by the test suite, which was green throughout.

So the rule stands, and the reason for it is amended: **the risk is not that documents lag code, it
is that assertions outrun verification.** A week is not the unit — a *check* is. Rewriting the rule
as "a claim is read back against its source before it is written down" would have caught all five;
rewriting it as "slow down" would have caught none.

### The sequence from here

| | objective | gate |
| --- | --- | --- |
| ✅ **W1** | **The corrections.** C1–C7. | done 2026-08-22 (#179) |
| ✅ **W2** | **Composition on the 11 shards.** Partition each shard's mean by evidence class. | done 2026-08-22 (#179) — and it went further than planned: the disclosure reached the explorer, the executive report, and finding 10 |
| 🔵 **W3** | **The portable object.** One click gives the figure, its breakdown and the pinned release. | **built, not landed** — [#180](https://github.com/raviaxo/RiskShard/pull/180) is open, and it **must not merge into a v0.10.0 world**: citations pin to a data-pack release whose frozen snapshot has no composition section, so the breakdown would travel with a link that disproves it |
| 🔴 **W3a** | **Cut the release that makes W3 honest.** | the data pack is byte-identical to v0.10.0 (`0ff2f12a5f6c`), so a release needs a data change first — the AU anchor (pending item 8) is the obvious and already-staged one |
| **W4** | **Arbitrary cells by nearest-shard borrowing.** | W3a, plus U2's three gates: an ADR-0009 amendment that does not exist, a stated failure condition, and borrowing-only |
| **W5** | **Reader context, client-side.** | W4 |
| **W6+** | **UI**, then reassess. | W5 |

**What changed in the gates.** W4's old gate cited ADR-0007 parts 2 and 3 as open. They closed on
2026-08-23 and **the restriction survives anyway**, on a better footing: assembly is blocked by a
missing instrument rather than an undecided policy, because a composed cell has no shard for
`module_coherence` to run over. **That lifts on a build.** Whoever wants bespoke assembly should
build composed-cell coherence, which is a smaller and far more tractable task than the debate it
replaces.

**Still not scheduled, and still deliberately:** contributions back to the ledger (piece E). It gets
decided with usage data or not at all.

---

### The original sequence, as written 2026-08-21

| week | objective | gate |
| --- | --- | --- |
| **W1** (from 2026-08-22) | **The corrections.** C1–C7. | none — do it |
| **W2** | **Composition on the 11 shards you already hold.** | C1, C4 |
| **W3** | **The portable object.** | W2 |
| **W4** | **Arbitrary cells by nearest-shard borrowing.** | W2, C2, C3 |
| **W5** | **Reader context, client-side.** | W4 |
| **W6+** | **UI**, then reassess. | W5 |

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
