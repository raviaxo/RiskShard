# Changelog

All notable changes to RiskShard are documented here. Versions follow a
practitioner-beta cadence: RiskShard is a working beta, **not** a finished or
human-certified product, and no grade in a release implies benchmark-grade —
that remains a recorded human review decision.

## v0.1.0 — 2026-07-21

First tagged stable practitioner beta. A coherent, self-consistent baseline
worth building on and sharing, with every number source-backed or honestly
labeled.

Data-pack release: `data_pack_releases/2026.07.21-v0.1.0-stable.json`
(69 files, fingerprint `ff9b713dd6a7…`).

### Coverage
- **11 country risk shards across 8 countries** (AU, CA, DE, FR, GB, JP, SG, US).
  **10 are 6/6 source-backed**; every business-email-compromise shard (US, AU, SG)
  is fully source-backed.
- **All 6 top-risk threats are runnable**, not merely evidenced: business email
  compromise, data breach, ransomware, insider misuse, and AI-enabled (deepfake)
  fraud calibrate and simulate cleanly; **third-party outage** calibrates with one
  honestly-labeled frequency estimate (`calibrated_with_assumptions`).
- **Conditional loss-chains** ([ADR-0001](docs/adr/0001-loss-chain-scenario-modeling.md)):
  a scenario can compose downstream conditional loss stages (e.g. a rare
  regulatory-penalty tail) gated by their own source-backed conditional probability.

### Claim discipline
- **Coherent maturity labels:** the "clears the automated gate" rung is standardized
  on `benchmark_review_candidate` (5 shards); `maturity_audit` reports **0 label/gate
  mismatches and no vocabulary drift**. Nothing is benchmark-grade.
- Insider Misuse and Third-Party Outage rest on source-backed frequency bridges plus
  **generic cross-cyber impact bridges**, loudly caveated as *not* threat-specific;
  both are tracked for dedicated impact evidence.

### Known limitations (loud, not hidden)
- `jp_manufacturing_ransomware_midmarket` is **4/6 (assumption-bridged)** and
  **scoped out of v1** as a labeled contribution scaffold — two frequency parameters
  remain estimates pending denominator-aware Japan evidence.
- The decision/controls engine is partially sketched and not production-ready.
- Full backlog and tracked gaps: [`docs/internal/NEXT_STEPS.md`](docs/internal/NEXT_STEPS.md).

### Gates at release
- `python -m unittest discover -s tests` → **147 tests pass**
- `validate_evidence.py`, `contributor_preflight.py`, `riskshard_doctor.py` → clean/pass
- `maturity_audit.py` → 0 mismatches
