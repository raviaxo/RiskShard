# AGENTS.md — operating rules for agents working in RiskShard

This is the agent-facing operating contract. It does not restate the contributor
rules — it points to their canonical owners and adds what an agent needs to work
here safely. **Read this before writing product code.**

## Session-open ritual (load-bearing)

Before editing anything, orient in this order:

1. **`AGENTS.md`** (this file) — operating rules and definition of done.
2. **`docs/internal/NEXT_STEPS.md`** — the internal working doc: restart point, current
   top blocker, canonical-owner pointers, maturity ladder, and the active work queue
   (one objective at a time). Capabilities live in the README; live coverage in the tools.

Then confirm repo reality (do not trust memory): `git log --oneline -5`,
`git status -s`, `git fetch origin && git log --oneline origin/main -3`, and verify
the environment is runnable (Python ≥ 3.9; activate `.venv`). State the **one**
objective for the session in a single sentence, name the files it touches, and
**wait for confirmation** before editing.

This ritual is the `/session:start` command (`.claude/commands/session/start.md`).

## Session-close ritual

Close a session with `/session:end` (`.claude/commands/session/end.md`). It verifies
the tree is clean and every unmerged branch / open PR is reported, proves the gates
are green (or names the reds), and reconciles `docs/internal/NEXT_STEPS.md` (queue,
restart point, top blocker) so the next `/session:start` boots clean. A session
is not "closed" until the tree is clean, open work is reported, and the owner docs
match reality.

## Definition of done

The canonical engineering rules and DoD live in
[`CONTRIBUTING.md`](CONTRIBUTING.md) — follow them. In short: **tests pass
(`python -m unittest discover -s tests`), `validate_evidence.py` is clean, and a
real run of the affected path succeeds.** For a content/evidence change also run
`contributor_preflight.py` and confirm the shard still calibrates and simulates.

## Rules that are easy to get wrong

- **One canonical owner.** Every fact has exactly one home. Do not duplicate
  capability lists, queues, or status across docs — point to the owner instead.
  (README owns "what works"; `docs/internal/NEXT_STEPS.md` owns the queue; `readiness_dashboard.py`
  owns live coverage.)
- **Caveats get louder, not quieter.** When you strengthen a parameter, make its
  limitations more visible, never less. Every number is source-backed or honestly
  labeled as an estimate/bridge.
- **Claim discipline.** "Automated benchmark-ready" is never "human-approved
  benchmark-grade." Preserve the maturity ladder everywhere results appear.
- **Any number in public text is generated or pinned by a test.** Not "kept current" —
  *generated*, or asserted against live data by something that fails. Three hand-written
  figures went stale inside one week (the social card's coverage line, twice; ADR-0018's grid
  counts; a roadmap figure), and the pattern is not carelessness: a number typed into prose has
  no owner and nothing watching it. If a figure cannot be generated, write the test that reads
  the document and checks it — `tests/test_cell_coverage.py` does exactly this for ADR-0018.
  **A rounded or narrated number counts.** "About a fifth" goes stale the same way.
- **Nothing public that couldn't be shown to a CISO tomorrow.** See
  [`docs/PUBLISHABLE_REQUIREMENTS.md`](docs/PUBLISHABLE_REQUIREMENTS.md).
- **One objective per session.** New important items go to `docs/internal/NEXT_STEPS.md`,
  not into scope.
- **Know what is out of scope.** [ADR-0009](docs/adr/0009-what-riskshard-is-and-is-not.md)
  decides it: RiskShard is a governed evidence commons, **not** a CRQ methodology project.
  Ask *does this make an existing published number more correct, or does it make the method
  more sophisticated?* The first is always in scope. The second is declined and recorded,
  however good the idea. In particular, a new declared axis may only be born from a defect
  **measured in our own data**, never from a good idea about measurement.
- **Strategic decision with no owner doc?** Surface it and stop — see
  `docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control.

## Commit posture

- Commit only when asked. Sign off every commit for the DCO: `git commit -s`.
- Default to a scoped feature branch (e.g. `shard/<area>`), not `main`. Do not push
  unless explicitly asked.
- **Docs-only changes may go straight to `main`** (owner's call, 2026-08-21). Docs-only
  means prose: `*.md`, ADRs, internal notes. It does **not** cover `evidence/`,
  `sources/`, `calibrations/`, `schemas/`, templates, or anything a generated page or a
  test reads — those keep the PR. Note what prose can still break: the README sold a
  framing ADR-0010 had retired for three months, and the social card carried a retired
  headline for twelve days. Speed here is a convenience, not a lower bar, so the gates
  still run and a stale claim is still a defect.
- Keep diffs scoped and coherent; standard-library-first; `scripts/` thin, logic in
  `engine/`.

## Where the rest lives

- How to contribute + the review bar: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- The model and its limits: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- A source taken end-to-end: [`docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md`](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
