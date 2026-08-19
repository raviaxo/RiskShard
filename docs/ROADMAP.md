# Roadmap

*Rewritten 2026-08-19. The previous roadmap planned new shard families and is archived as
[declined](internal/declined_emergent_risk_scenarios.md) — it failed the
[ADR-0009](adr/0009-what-riskshard-is-and-is-not.md) test. This one has an end. Every milestone
is a number you can check without asking us, and the last one has a date that
[ADR-0017](adr/0017-the-kill-criterion-gets-a-clock.md) already committed to in writing.*

## What this project is finishing

**The audit.** Reading every public cyber-loss source we cite, one at a time, and recording what
each one actually publishes. Not more sources — *these* sources, finished.
[ADR-0016](adr/0016-the-audit-is-the-product.md) makes it the only growth surface.

---

## M1 — Finish the audit · 58 → **72 of 72** · target 2026-09-15

Every registered source read on all four properties: does it publish a **mode**, a
**distribution**, an **exceedance statement**, and can you **name the population** it measured.

| | |
| --- | ---: |
| sources read on all four properties | **58 of 72** |
| answers verified against a stored artifact | **232 of 288** |
| sources held only as a pointer, needing a person | **14** |

**14 sources is the whole of M1**, and it is the one milestone an agent cannot finish alone —
these are registration-gated documents someone has to request. Three carry most of the value:
Cyentia IRIS 2025 (likeliest in the corpus to publish an actual distribution *and* exceedance),
IBM Cost of a Data Breach 2025 regional cuts (the most-cited cyber loss figure in the world, and
we hold only coverage *about* it), and Sophos State of Ransomware 2025 global (three shards lean
on it; we have never read the full report).

**Done means:** `riskshard_doctor.py` prints 72 of 72, and the phrase *"the audit is complete"*
becomes true and publishable. It is a headline exactly once.

## M2 — Publish the audit as its own artifact · target 2026-09-30

The audit currently lives in `sources/audit.yaml`, a machine file. **The finding is public and the
evidence for it is not readable**, which is the gap between having done the work and having
published it.

**Done means:** a citable page — 72 sources × 4 questions, each answer carrying the quoted passage
and the document hash — that a stranger can link to, cite, and dispute row by row without cloning
the repo.

## M3 — Write the labelling standard as a spec · target 2026-10-31

The four questions, formalised so a third party can apply them to sources we have never read. This
is what turns *our audit* into *a standard*, and it is the only path off depending on one person's
reading.

Includes the amount **shape** / **treatment** split
([`amount_shape_design_input.md`](internal/amount_shape_design_input.md)) — the first externally
contributed design input this project has had, and still blocked on one question to its author.

**Done means:** someone outside the project can label a source they found themselves and the label
means the same thing ours does.

## M4 — The registry decision · **2026-11-01, fixed**

[ADR-0017](adr/0017-the-kill-criterion-gets-a-clock.md) pre-committed this date and states in
writing that **it does not move again**. At the first release on or after 2026-11-01, count:

1. shards whose `impact.max` cites a registry entry — **0 today**
2. entries contributed by anyone outside the project — **0 today**

If neither has moved, the registry retires. **No external readership at the date is not grounds
for another extension** — it is grounds for retiring it and publishing that the trial never got a
fair test. The doctor prints the date on every run.

## M5 — The adoption test · measured at M4

Whether any of this is used, stated as numbers rather than impressions:

- has anyone **cited** a parameter or the audit?
- has anyone **disputed** a row?
- has anyone **applied the standard** to a source we did not read?

All three read zero today. Published either way.

---

## What this roadmap declines

Recorded rather than left implicit, because every one of these is a good idea and good ideas are
how this project loses focus. [ADR-0009](adr/0009-what-riskshard-is-and-is-not.md): *a new declared
axis may only be born from a defect measured in our own data, never from a good idea about
measurement.*

- **More shards, countries, or threat families.** Coverage is not the constraint; the audit is.
- **New emergent scenario families** — AI-as-liability, systemic loss, regulatory loss.
  [Archived here](internal/declined_emergent_risk_scenarios.md) with the reasoning intact.
- **A better engine, or engine features.** It exists to expose defects in the anchors, and it does
  that already.
- **A CRQ methodology.** ADR-0009 settled it.
- **Bringing back the reader-target selector.** [ADR-0018](adr/0018-the-target-selector-failed-measurement.md)
  retired it on a measurement and set two conditions for reconsidering, both false today. No two
  facet values may each answer alone and answer nothing together (60 pairs do). And a majority of
  targets must answer something (83 of 539 do, which is 15%). Coverage has to move first, and
  coverage is not what this roadmap is buying.
