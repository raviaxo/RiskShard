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
- **Nothing public that couldn't be shown to a CISO tomorrow.** See
  [`docs/PUBLISHABLE_REQUIREMENTS.md`](docs/PUBLISHABLE_REQUIREMENTS.md).
- **One objective per session.** New important items go to `docs/internal/NEXT_STEPS.md`,
  not into scope.
- **Strategic decision with no owner doc?** Surface it and stop — see
  `docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control.

## Commit posture

- Commit only when asked. Sign off every commit for the DCO: `git commit -s`.
- Default to a scoped feature branch (e.g. `shard/<area>`), not `main`. Do not push
  unless explicitly asked.
- Keep diffs scoped and coherent; standard-library-first; `scripts/` thin, logic in
  `engine/`.

## Where the rest lives

- How to contribute + the review bar: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- The model and its limits: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
- A source taken end-to-end: [`docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md`](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
