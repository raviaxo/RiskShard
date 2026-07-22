# PUBLISHABLE_REQUIREMENTS — the public-surface bar and change control

What has to be true before anything in RiskShard is shown publicly, and how
strategic changes to that bar are decided.

## The public-surface bar

Nothing goes on a public surface (README, docs, console output, exported reports,
released data packs) unless it clears every line below:

1. **CISO-safe.** Nothing public that couldn't be shown to a CISO tomorrow.
2. **Every number is traceable or labeled.** A value is either source-backed to a
   reviewed public source, or honestly labeled as an estimate / cross-context
   bridge. Nothing is dressed up as a local claim.
3. **Caveats are louder, not quieter.** Limitations travel with the number wherever
   it appears.
4. **Claim discipline.** "Automated benchmark-ready" is never "human-approved
   benchmark-grade." The maturity ladder (see the [README](../README.md) → "What
   RiskShard is — and isn't") stays visible.
5. **Methodology-honest.** Claims respect the model's stated limits
   ([`METHODOLOGY.md`](METHODOLOGY.md)) and do not overclaim precision.
6. **Gates pass.** Tests, `validate_evidence.py`, and `contributor_preflight.py`
   are clean; a real run of the affected path succeeds.

The contributor-facing version of this bar (how a submission is reviewed) lives in
[`../CONTRIBUTING.md`](../CONTRIBUTING.md) → "How your contribution is reviewed."
This file is the canonical owner of the *bar itself*; CONTRIBUTING points to it.

## Change Control

The bar above and other strategic choices (schema direction, maturity definitions,
what counts as benchmark-grade, licensing posture) change only through a recorded
decision with a named owner doc.

- If a change to the bar is needed, record the decision and its rationale in the
  owning doc before acting on it.
- **If a strategic decision is needed and no owner doc records it: surface it and
  stop.** Do not infer policy silently. The session ritual (`../AGENTS.md`) depends
  on this rule.

Day-to-day work items are not strategic decisions — those go to
[`NEXT_STEPS.md`](internal/NEXT_STEPS.md).
