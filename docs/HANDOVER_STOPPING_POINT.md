# HANDOVER — restart point and top blocker

This is a thin pointer. The authoritative, always-current restart point is the
active objective in [`NEXT_STEPS.md`](NEXT_STEPS.md). Update that file as work
moves; keep this one short.

## Where to restart

Open [`NEXT_STEPS.md`](NEXT_STEPS.md) and work the first objective that is not yet
marked done, one at a time, to its Definition of Done (see [`../AGENTS.md`](../AGENTS.md)).

## Current top blocker

*Updated 2026-07-20.*

The 2026-07-19/20 session was large and is fully merged (PRs #18–#33, all CI-green). It
cleared the readiness P1/P2/P3 queue and then went further:
- **BEC:** US, AU, SG shards all 6/6 source-backed.
- **Top-risk threats evidenced (6/6 direct):** Insider Misuse, Third-Party Outage.
- **Emergent program:** `docs/ROADMAP.md` + first emergent threat `ai_enabled_fraud` (deepfake fraud).
- **Loss-chains (ADR-0001, fully implemented):** schema `loss_stages` + engine composition +
  worked example (UK breach → ICO regulatory penalty) + per-stage evidence/report provenance +
  calibration-profile generation. See `docs/adr/0001-loss-chain-scenario-modeling.md`.
- Ritual owner docs restored; data-pack release `2026.07.20-us-bec-source-backed` cut.

**No active objective and no blocker.** Next work is forward-looking, from `NEXT_STEPS.md` /
`ROADMAP.md` (pick any):
- Roadmap builds: correlated single-vendor outage, EU AI Act penalty, regulatory enforcement
  (buildable as standalone threats or loss-chains).
- Maturation: calibration profiles for the three evidenced top-risk threats
  (`ai_enabled_fraud`, Insider Misuse, Third-Party Outage); finish
  `jp_manufacturing_ransomware_midmarket` (4/6).

No strategic decision is currently blocked. If one arises with no owner doc to
record it, surface it and stop — see
[`PUBLISHABLE_REQUIREMENTS.md`](PUBLISHABLE_REQUIREMENTS.md) → Change Control.
