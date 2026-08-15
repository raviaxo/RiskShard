# ADR-0016 — The source audit is the product; the shards are the demonstration

- **Status:** Accepted (2026-08-15)
- **Date:** 2026-08-15
- **Deciders:** repo owner
- **Extends:** [`0006-depth-over-breadth.md`](0006-depth-over-breadth.md) (depth over breadth, now
  applied to the whole programme rather than to shard selection),
  [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md) (the governed evidence object is
  the product — this is that argument one level up)
- **Related:** [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md)
  (scope gate), [`0015-the-source-audit.md`](0015-the-source-audit.md) (the audit itself),
  [`0012-loss-event-registry-bounded-trial.md`](0012-loss-event-registry-bounded-trial.md)
  (the trial this makes a decision about at v0.9.0)

## Context

Eight months of work has produced 46 engine modules, 27 scripts, 342 tests, 15 ADRs, 261 evidence
records, 61 registered sources, 16 calibrations and 20 scenarios — built and maintained by one
person.

It has produced **2 stars, 0 forks, 0 outside contributors, 0 registry citations and no known
external user.**

That gap has been read as a distribution problem for some time. It is not. It is a **shape**
problem, and the ADR-0015 audit exposed it within six source reads.

### The shards are in the worst available position

**11 cells is simultaneously too many to maintain and too few to be useful.** No practitioner's
context is one of our eleven cells, so the shards answer nobody's actual question; and the
maintenance is compounding, because 61 sources — 10 of them already flagged on rolling URLs — each
publish annually, and an edition change can invalidate parameters across several shards at once.

The shards' own headline is now, correctly, *7 of 66 parameters are drawn from the population they
are used for* ([finding 4](../FINDINGS.md)). That is the honest number and it is the right one to
publish. It also means the shards demonstrate a method rather than deliver a result.

### The audit has the opposite shape

|  | shards | source audit |
| --- | --- | --- |
| useful to | practitioners in our 11 cells | anyone doing CRQ, whatever their model |
| can it be finished | no | **yes — 61 rows** |
| maintenance | sources × parameters, compounding | one row per source, per edition |
| staleness detection | manual | **mechanical** (artifact hash, ADR-0015) |
| exists elsewhere | several comparable efforts | **nowhere** |

Six reads in, the audit has already published a result nobody else holds, **corrected our own
framing before it was said publicly** — "public sources publish only point statistics" is false —
and surfaced an exceedance statement sitting unused inside our own corpus.

## Decision

**The source audit is what RiskShard offers. The shards are the demonstration that the method
works, and they stop growing.**

### 1. The audit is the growth surface, and it is the only one

New work adds rows to a finite table. The test for any proposed objective is now:

> Does this add a row to a finite table, or a parameter to an infinite one?

The second is declined and recorded, however good the idea — the same discipline
[ADR-0009](0009-what-riskshard-is-and-is-not.md) applies to measurement axes, applied to programme
scope.

### 2. Shard coverage freezes at 11

No new cells, no new countries, no new threats. Existing shards are maintained for correctness —
a source correction still gets made — but breadth is closed. This is
[ADR-0006](0006-depth-over-breadth.md) honoured rather than extended: depth over breadth was always
the rule, and adding cells was the drift.

Retiring shards is permitted and expected. The JP scaffold, already scoped out of v1, is the
obvious first candidate.

### 3. The engine, simulation and console are frozen

Bug fixes and correctness only. [ADR-0010](0010-where-riskshard-stops.md) already made the
simulation a reference rendering; this stops maintaining it as though it were a product.

### 4. What we ask contributors for changes

Until now the ask has been a shard or a source-backed parameter — a week of work, which is why
nobody has done it. **The ask becomes an audit row**: read one source, answer four questions, quote
the passage. That is twenty minutes, it is checkable against the artifact hash, and it is
work a practitioner can do while doing their own job.

### 5. The artifact is citable, not readable

The audit ships as a versioned, DOI-bearing reference pinned to a data-pack fingerprint, built to
be cited in a methodology document or a procurement argument rather than read once. Reach is
measured as **citations by people who are not us**, not as stars.

## Consequences

- **Most of the roadmap is now out of scope**, including work that was queued and defensible. New
  countries, new threats and the benchmark programme's expansion are all closed by part 1.
- **The maintenance treadmill slows sharply.** A source publishing a new edition invalidates one
  audit row, detectably, rather than an unknown set of parameters silently.
- **The published headline changes.** RiskShard becomes *"what public cyber-loss sources actually
  publish, verified"* rather than *"governed parameters for eleven cells"*.
- **The shards get more valuable by being frozen**, not less: they become the worked example that
  proves the audit's questions are the ones that matter, and their defects are the evidence.
- **This is the fifth framing correction in eight days.** The rate is what publishing your reasoning
  looks like; each one was measured rather than argued.

## Alternatives considered

- **Keep both, audit leads.** The safer option and the one that keeps optionality. Rejected because
  optionality is what produced the current surface: every axis stayed open, one person maintains
  all of them, and the result is zero adoption with a compounding cost base.
- **Shards stay primary.** Defensible if the shards' value is real and merely undiscovered. Rejected
  on the measurement: eight months, no external user, and a headline that honestly reports 7 of 66.
- **Widen the audit to sources we do not hold.** Rejected for now under
  [ADR-0015](0015-the-source-audit.md) part 5 — it converts a completable table into a source-hunting
  project, which is the shape being escaped.
- **Stop the project.** Recorded because it deserves to be. Rejected: the audit is a genuinely
  unfilled gap, two independent practitioners have said so unprompted, and it is finishable by one
  person — which none of the alternatives above are.

## Open questions

1. **Does the loss-event registry survive?** ADR-0012's kill criterion is measured at v0.9.0 and
   both metrics read 0. Under this ADR the registry is a second growing surface, which part 1
   disallows — but the decision belongs to the criterion already recorded, not to this ADR.
2. **Do the shards eventually retire entirely?** Not decided. They currently earn their place as
   the demonstration; whether that stays true once the audit is complete is a question for then.
