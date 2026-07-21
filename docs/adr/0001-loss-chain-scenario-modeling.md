# ADR-0001 — Loss-chain scenario modeling

- **Status:** Proposed (awaiting owner acceptance)
- **Date:** 2026-07-20
- **Deciders:** repo owner
- **Related:** [`../ROADMAP.md`](../ROADMAP.md) (Family C + the loss-chain thesis)

## Context and problem

Today a scenario is a **single event with a single loss magnitude**
(`schemas/shard_schema.json`): `frequency{min,likely,max}` × `impact{min,likely,max}`,
run through PERT/triangular Monte Carlo, aggregated by summing across scenarios.

But the loss a board actually fears is a **chain**: one initiating event cascades into
several *conditional* loss forms — a breach → (maybe) a regulatory penalty → (maybe)
securities/disclosure liability → (maybe) an insurability gap → (maybe) personal officer
liability. The current schema can express the *initiating event* well and nothing after it.
A threat-label library cannot express the cascade; expressing it is the roadmap's central
differentiation.

**The binding constraint is evidence, not engineering.** RiskShard's whole value is that
every number is sourced or honestly labeled. Marginal frequencies and impacts are
sourceable (we have done it 14× this program). **Conditional** probabilities
(`P(fine | breach)`, `P(suit | disclosure)`) and **correlations** (cyber-catastrophe) are
far scarcer. So the real question is not "can we build chains" (the Monte Carlo engine
already can) but "**how far can we chain and still source it honestly**."

## Decision drivers

1. **Differentiation** — loss-chains are what point-tools structurally cannot express.
2. **Evidence-sourceability** — the binding constraint; conditional/correlation data is scarce.
3. **Engine reuse** — Monte Carlo + portfolio aggregation already exist; composition is cheap.
4. **Backward compatibility** — 11 country shards + 6 top-risk threats run on the current schema; do not break them.
5. **Explainability** — a board/CISO must be able to read the cascade and its provenance.
6. **Honesty over precision** — never let a chain manufacture spurious precision from weak conditional data.

## Options considered

**Option 0 — Status quo.** Keep single-threat; model each loss form as its own scenario and
sum in the portfolio. *Pro:* zero change, fully honest. *Con:* cannot gate one loss on
another (portfolio sum assumes independence and co-occurrence); not differentiating.

**Option 1 — Additive loss-mode composition.** A scenario carries several loss *components*
(direct + response + regulatory), each its own distribution, summed per trial — but all
assumed to occur given the event. *Pro:* small schema change, marginals are sourceable.
*Con:* no conditionality — it *overstates* by assuming every loss mode always fires.

**Option 2 — Staged conditional loss-chain (bounded).** A scenario keeps its current
frequency+impact as the initiating stage; it *may optionally* declare ordered downstream
`loss_stages`, each with a **sourced conditional probability**, an impact distribution, a
`loss_mode`, and its own evidence. Composed per Monte Carlo trial (Bernoulli gate × PERT).
Depth capped (≤3 stages) initially. *Pro:* expresses the real cascade; most differentiating;
engine handles it; each stage independently governed. *Con:* conditional-probability
evidence is scarcer — rollout must be gated per link on data availability.

**Option 3 — Full DAG + cross-scenario correlation (cyber-cat).** Arbitrary graphs plus
correlated aggregation across scenarios. *Pro:* maximal power (systemic/catastrophe modeling).
*Con:* correlation cannot be sourced honestly today; large engine change; explainability drops.
Over-engineered for now.

## Decision (recommended)

Adopt **Option 2, bounded** — a staged conditional loss-chain as an **optional,
backward-compatible** schema extension.

- Existing scenarios are unchanged; `loss_stages` is optional. The current `frequency`/`impact`
  remain the initiating stage.
- Each `loss_stage` requires: a `loss_mode` label, a **conditional probability** (sourced or
  explicitly labeled estimate), an impact distribution (`min/likely/max`), and per-stage
  evidence + confidence — the same discipline as every other number.
- Cap depth at ≤3 stages while the pattern is unproven.
- **Prove it on one link first:** an initiating breach/BEC event → a **regulatory-penalty**
  stage, where the conditional `P(enforcement | event)` is derivable from published
  enforcement/fines data. Ship it as `governed_starter`, loudly caveated, before generalizing.
- **Defer** cross-scenario correlation / cyber-catastrophe (Option 3) to a **future ADR**,
  taken only once the staged model is proven and correlation evidence exists.

**Why not the others:** Option 0 doesn't differentiate; Option 1 overstates by forcing all
loss modes to co-occur; Option 3 can't be sourced honestly yet and hurts explainability.

## Guardrail — the evidence rule for stages

No loss stage ships without (a) a conditional probability that is source-backed or labeled
`estimated`/`bridge`, (b) a source-backed or labeled impact distribution, and (c) a per-stage
confidence. The composed result must surface **per-stage provenance** (which numbers are
sourced, which are bridges) — no hidden conditional or correlation assumptions. A chain whose
conditional links are weak is labeled low-confidence, not dressed up.

## Consequences

**Positive:** board-legible cascades with provenance; reuses the Monte Carlo + aggregation
engine; backward-compatible (existing 17 scenarios untouched); each stage independently
governed; opens Family C (regulatory/governance loss) which no cyber tool quantifies.

**Costs / negative:** schema v2 (`loss_stages`), engine stage-composition, calibration-profile
and report changes; conditional-probability evidence is scarcer, so the build is gated per link
on data; validation and explainability are more complex; genuine risk of spurious precision
from weak conditional data — mitigated by the guardrail above.

**Follow-ups if accepted:**
1. Schema v2 — optional `loss_stages` on `shard_schema.json` (+ evidence-record support for conditional probabilities).
2. Engine — per-trial stage composition (Bernoulli gate × existing PERT draw).
3. Calibration + report — surface per-stage provenance and confidence.
4. First worked example — a regulatory-penalty stage on an existing breach shard.
5. A future ADR for correlation / cyber-catastrophe (Option 3).

## Open questions (deferred)

- Ordered linear chain vs. DAG (start linear; revisit if a real scenario needs branching).
- How to source conditional probabilities beyond the regulatory link (litigation rates,
  insurability-denial rates) — treat each as its own evidence-gathering objective.
- Correlation / aggregation across a portfolio — explicitly out of scope here; future ADR.
