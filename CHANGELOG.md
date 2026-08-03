# Changelog

All notable changes to RiskShard are documented here. Versions follow a
practitioner-beta cadence: RiskShard is a working beta, **not** a finished or
human-certified product, and no grade in a release implies benchmark-grade —
that remains a recorded human review decision.

## v0.3.0 — 2026-08-02

The residency release. Every change since v0.2.0 moves evidence closer to the
population it claims to describe — and takes the cost of that trade openly,
including a maturity demotion the automated gate demanded.

Data-pack release: `data_pack_releases/2026.08.02-v0.3.0.json`.
Ledger tick since v0.2.0: **cell-matched 28 → 31 · cross-country bridges 26 → 20**.

### Canada: both sides of the shard move to Canadian data
- **Frequency** moved to Statistics Canada CSCSC full-cell readings (finance ×
  medium × steal-personal/financial-info): 0.15 / 0.201 / 0.273 replacing the
  OPC/CIRA all-organization anchors — three parameters flipped to cell-matched.
  The stress cell carries StatCan quality code C ("use with caution") on its face,
  with the quality-B alternative documented on the record.
- **Impact** moved to NetDiligence Claims-from-Canada insured-claims anchors:
  floor USD 66K (Hacker-cause average, N=8), stress USD 15M (dataset maximum,
  N=84), replacing both Cyentia global bridges. Thin cells are carried loudly;
  threat stays bridged (cause taxonomy is not confirmed compromise). Simulated
  CA range narrowed because the evidence got closer to home.

### Australia ransomware: four country bridges retired
- Frequency moved to the Australian readings of the Sophos State of Ransomware
  surveys — likely **0.54** (2024, n=330), stress **0.70** (2023, n=200; no longer
  a duplicate of the likely anchor). Typical loss moved to the Sophos *State of
  Ransomware in Australia 2025* mean recovery cost (**USD 0.65M**, excluding
  ransom payments — exclusion carried loudly). The stress loss is now Latitude
  Group's ASX-disclosed **AUD 76M** cyber-incident cost — a documented Australian
  financial-services extortion loss replacing a global percentile bridge at
  nearly the same level.
- **The trade's cost, taken openly:** the Australian anchors are all-sector, so
  the shard fell below the automated benchmark gate's industry-relevance minimum
  and is relabeled `benchmark_review_candidate` → `governed_starter`
  (benchmark-ready 5 → 4) rather than over-claiming.
- **Edition-roll catch:** Sophos's live 2024 whitepaper URL now serves the 2025
  edition under the 2024 filename — the same silent roll previously recorded for
  IBM. Both global Sophos editions are pinned to immutable Internet Archive
  snapshots, with every cited line verified in the gathered artifact.

### Machinery
- New `public_zip` access mode (StatCan full-table downloads), with the
  content-type guard extended and tested.
- `company_disclosure` added to the controlled source-type vocabulary (Latitude
  ASX disclosure; any future issuer filings share it).
- Three superseded legacy `estimated` records removed from the AU ransomware
  evidence file — the pack's evidence-type counts no longer carry placeholder
  assumptions that nothing selects.

## v0.2.0 — 2026-08-01

The correction release. Most of what shipped since v0.1.0 exists to make the
numbers harder to rebut — including where that meant retracting our own figures
and deliberately making the headline smaller.

Data-pack release: `data_pack_releases/2026.08.01-v0.2.0.json`
(90 files, fingerprint `9d006267794a…`).

### Corrections (the point of this release)
- **Retracted the insider-misuse 66%/76% frequency pair** — those figures appear
  in no primary source. Replaced with artifact-backed values from the same survey
  family: `frequency.min` **0.51** (six-or-more-incidents hard floor),
  `frequency.likely` **0.83** (Gurucul 2026's 2024 reading); `frequency.max` 0.90 kept.
- **Reattributed the AI-fraud `impact.likely` to Regula at USD 450k** — the
  previously cited $500k/$603k pair was never on the cited page.
- **Re-anchored BCI third-party-outage evidence to its own news release** (an
  immutable snapshot carrying both cited figures); values unchanged.
- **Regenerated the insider-misuse top-risk scenario**, which was still simulating
  pre-correction impacts — it sat outside the calibration-drift gate's coverage
  (top-risk scenarios are not risk modules; extending the gate is tracked).

### The headline now tells the truth about populations (ADR-0003, parts 1–2)
- Every source-backed record declares `population_match` (schema-required), and a
  country-strict check classifies each parameter as **cell-matched** (evidence from
  the shard's own population cell) or **bridged**. The public headline split from
  "66/66 source-backed" to **28 cell-matched · 38 bridged (26 cross-country) of 66**
  — smaller on purpose; the explorer, evidence report, and provenance CLI all
  carry the per-parameter status.
- **The strength ledger now records the split** per release (new
  `params_cell_matched` / `params_cross_cell` / `params_cross_country` metrics),
  so retiring a bridge is a measured tick, not an assertion. Pre-split entries
  are never compared against the new metrics (no fabricated deltas).

### Evidence integrity
- **Full source sweep (2026-08-01):** all 52 registered sources re-gathered and
  diffed — **no cited figure has drifted** — but six artifacts had never actually
  evidenced their cited line. Four fixed with verified stable artifacts
  (archive.org snapshots, the SUSB workbook, ABS re-pinned off `/latest-release`);
  two recorded as KNOWN GAPs rather than papered over.
- Every source now carries **`url_stability: dated | rolling`** (44 dated /
  8 rolling) after `ibm.com/reports/data-breach` silently began serving the next
  edition under a prior-year citation.
- `gather_sources.py` refuses artifacts that do not match their declared
  `access_mode` — a landing page can no longer silently replace a cited PDF.

### Citability and reproducibility
- **Citable parameter identifiers** (ADR-0004): `RS:<shard>/<parameter>@<release>`
  pinned to immutable fingerprinted releases, with archived per-release explorer
  pages, an alias map so renames cannot break written-down citations, and a
  "cite this number" affordance that carries the caveat inside the citation.
- **Cross-machine reproducibility** (ADR-0002): scenario seeds no longer depend on
  the repo's absolute path; published numbers reproduce on any machine, pinned by
  a golden-value test across Python versions. Every loss figure moved once (<2%),
  recorded in `revisions/` and explained on the explorer.

### Coverage and machinery
- `jp_manufacturing_ransomware_midmarket` closed 4/6 → 6/6 — **all 11 shards
  source-backed** (the v0.1.0 known limitation).
- Insider-misuse impact rests on Ponemon 2023 insider-specific costs (2 of 3
  generic cross-cyber bridges retired).
- CI now enforces the definition of done: contributor preflight, the
  calibration-drift gate, and a secret scan run on every PR (both new gates
  verified to fail, not merely to run).
- **Challenge-a-number**: `provenance` shows value + source + exact cited line +
  caveat per parameter; `--dispute` pre-fills a GitHub issue. Portfolio-wide
  evidence report and pyfair export shipped alongside.
- Public explorer at <https://raviaxo.github.io/RiskShard/> rebuilt in the
  regulatory-filing identity; per-release archived copies under `docs/r/`.

### Known limitations (loud, not hidden)
- Only GB is fully cell-matched; the bridged map (SG 4, CA 5, JP 5,
  AU-ransomware 6, US-frequency 3) is the declared work queue.
- Per-cell loss magnitude largely does not exist publicly; impact evidence
  remains the structural gap (ADR-0003 declares it rather than hiding it).
- Two KNOWN-GAP artifacts from the source sweep are documented in
  `docs/internal/source_sweep_2026-08-01.md`.
- Nothing is benchmark-grade; the automated gate's best rung remains
  `benchmark_review_candidate`.

### Gates at release
- `python -m unittest discover -s tests` → **220 tests pass**
- `validate_evidence.py`, `contributor_preflight.py`, calibration-drift gate,
  `riskshard_doctor.py` → clean/pass

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
