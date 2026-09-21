# ADR-0020 — A publisher left out on purpose is declared, never silent

**Status: Accepted** (2026-09-21)

## Context

The corpus is an enumeration of the sources a practitioner reaches for, and
[ADR-0015 §5](0015-the-source-audit.md) is explicit that it is **not a census of public
cyber-loss evidence**: *"No published sentence may imply otherwise."* So a publisher's absence
has never been a claim about that publisher, and the registry has never owed the world a reason
for every report it does not hold.

That covers absence by scope. It does not cover absence by **decision**, and one now exists: the
maintainer has a conflict of interest for a publisher whose reports are widely circulated in the
pool this project asks readers to draw from. The `read_a_source` route invites a stranger to bring
a report we have not read, so the question is not hypothetical and it is not ours to time — the
first submission decides it in public, on someone else's schedule.

**Two arguments were available and both are wrong.**

- *"It publishes no loss magnitude, so it is out of scope."* **13 of the 65 sources read publish
  nothing on all four properties** — a prudential standard, a statute, a fines page, state
  guidance, single-company results, a press report. This corpus deliberately admits sources that
  yield no usable quantity, because *what a source does not publish* is the finding. Excluding one
  publisher on that ground would contradict thirteen rows we already keep.
- *"Register nothing and say nothing."* The project's entire offer is **check us rather than trust
  us**. An undisclosed narrowing of an enumeration is the one defect that discredits the standard
  itself rather than a single number, and it would have to be disclosed the first time anyone
  asked — which is worse than disclosing it first.

## Decision

**A publisher may be excluded from the registry, and every exclusion is declared in
`sources/registry.yaml` under `exclusions:`, carrying the publisher, the scope, the reason and the
date it was decided.** The audit page publishes them and the doctor counts them.

Declared today: **CrowdStrike, all publications, maintainer conflict of interest, 2026-09-21** —
decided before any CrowdStrike source had been registered or submitted, and before any answer
about one had been published.

**What an exclusion is not.** It is not a judgement about the publisher, their methodology or
their reports; the audit does not grade accuracy ([ADR-0015](0015-the-source-audit.md)) and this
records even less than that. It is a statement about **who is reading**, not about what was read.

**The honest answer to a submission is this entry, not silence.** If a reader sends a source from
an excluded publisher through the read-a-source route, they get pointed here.

## How it is enforced, rather than remembered

Three stale copies of this project's own headline survived a month because nothing failed when they
drifted, so this decision ships with its own failure conditions:

- **`audit_defects` fails** if a registered source's publisher is declared excluded, and if an
  exclusion entry is missing its publisher, reason or date. A defect fails the doctor.
- **The audit page prints every exclusion** with its reason and date, and the count sits in the
  same facts table as the coverage — so the gap is as visible as the numbers.
- **A test ties the data to this file**: every declared publisher must be named in this ADR, so an
  exclusion cannot be added quietly in a data file.

## Alternatives considered

- **Audit the publisher normally, with the conflict disclosed on the row.** Stronger on integrity
  and rejected only on the maintenance condition ADR-0012 already recorded as unmet: there is no
  second maintainer, so a conflicted judgement would be reviewed by nobody. **This remains the
  upgrade path** — if a second reader appears, an exclusion should be reconsidered as a disclosed
  audit rather than kept for convenience.
- **Silent omission.** Rejected above.
- **Exclude the whole subject class (threat-telemetry reports).** Rejected: it contradicts thirteen
  registered rows, and dressing a conflict as a scope rule is the dishonest version of this ADR.

## Consequences

- **The corpus has a stated, countable hole**, which is a cost paid deliberately. The enumeration
  claim in ADR-0015 §5 still holds, and now says where it was narrowed on purpose.
- **A reader can audit the audit's own scope**, not just its answers.
- **It invites the obvious inference** about why the maintainer is conflicted. That is accepted:
  the alternative is a gap with no explanation, which invites a worse one.
- **Removing an exclusion is a decision too.** It is an amendment here, not a data edit.
