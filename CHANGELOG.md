# Changelog

All notable changes to RiskShard are documented here. Versions follow a
practitioner-beta cadence: RiskShard is a working beta, **not** a finished or
human-certified product, and no grade in a release implies benchmark-grade —
that remains a recorded human review decision.

## Unreleased

### ADR-0008 commitment 1 — every maximum now declares what it bounds
- `exceedance_basis` is in the schema and **required on any record whose parameter is an
  impact maximum**, with `exceedance_detail` required whenever the basis claims a quantile
  or a rank — so a quantified claim cannot ship without its number. All 20
  maximum-anchoring records declared. Verified to fail on a stripped declaration.
- `engine/exceedance.py` measures it; `riskshard_modules.py exceedance` reports it; the
  explorer gains a cover fact, a per-anchor `exceedance` line and a Note 1 paragraph; the
  evidence report gains a headline, an `Exceedance` column and a per-shard callout. Each
  surface is pinned by a test **verified to fail** when that surface is stripped, and
  rendering was confirmed live in-browser (11 exceedance lines for 11 maxima).
- **The measurement beat the prediction.** ADR-0008 expected `none_known` on nearly
  everything. Actual, across the 11 selected maxima: **0 modeled quantiles · 2 observed
  ranks · 2 legal ceilings · 7 none_known.** US and CA data breach *did* admit an empirical
  exceedance — rank 1 of N=579 and rank 1 of N=84 — because their sources state N and nobody
  had written the ratio down. Both are declared as a **floor, not an estimate**: they are
  within-sample rates on insured claims, so policy limits and uninsured losses mean the true
  rate above those values is *higher*, not lower. The ADR was corrected to match rather than
  the finding being trimmed to fit the ADR.
- The load-bearing claim — **no maximum in this portfolio is a modeled quantile** — is now
  pinned by a test instead of a memo.
- **Caught by the suite, not by review:** the schema rule broke the contributor path —
  a freshly scaffolded pack emitted an `impact.max` placeholder with no declaration and
  failed its own preflight. Both scaffold generators now emit `exceedance_basis:
  none_known` for maxima, which also puts the question in front of a contributor rather
  than behind them. `CONTRIBUTING.md` and the content checklist say when and how to claim
  something stronger.

## v0.5.0 — 2026-08-07

The governed tail. Three people who do not know each other pushed on RiskShard
from three directions in four days, and all three turned out to be pushing on the
same joint: **the maximum**. This release records what that costs, corrects the
last anchor that could not be defended, and pins citations to current reality —
`RS:` identifiers resolved to `v0.4.0` and therefore predated everything shipped
on 2026-08-07.

Data-pack release: `data_pack_releases/2026.08.07-v0.5.0.json`.
Ledger tick since v0.4.0: **no count moved** — cell-matched stays 31, cross-country
stays 15. This release moved a construct, not a number, and the ledger says so
rather than manufacturing progress.

### ADR-0008 — a maximum must say what it bounds (Accepted)
- Measured across all 11 shards: `impact.max` is a modeled quantile in **0 of 11**.
  Every one is a single documented event (4), a dataset extremum (4), a statutory
  cap (2) or an issued penalty (1). **Not one carries an exceedance probability.**
- `frequency.max` is `org_prevalence_incident` in **11 of 11** — the same construct
  as its own `frequency.likely`. The portfolio's notion of "stress" is a bigger
  reading of the same survey plus one anecdote.
- This is not cosmetic. The [worked decision](docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md)
  measured it: the per-event mean is **14.8× its own mode** because the maximum
  drives the distribution instead of bounding it, and moving that one anchor swings
  P(event > AUD 20M) from **0% to 23%**.
- The decision: a third declared axis (`exceedance_basis`), where `none_known` is a
  legal and currently common value that must appear on the face of the number.
  It answers the tail half of [ADR-0007](docs/adr/0007-construct-coherence.md)'s
  open question 1; which *mixes* are acceptable remains open.
- **Nothing is built yet.** v0.5.0 carries the decision, not an implementation.

### Australia BEC: the last construct-inappropriate anchor is corrected
- `impact.max` moves from AUD 2,000,000 — the ACCC's *national aggregate* of all
  small-business false-billing losses for the year — to AUD 2,668,483, one
  documented Australian BEC event reported by the AFP (two transfers of $519,545
  and $2,148,938, September 2020). A whole-country loss total is not a quantity a
  single firm can incur; it also sat *below* the real documented Australian tail.
- Modeled gross although AUD 2.1M of AUD 2.6M was recovered, matching the Coalition
  funds-transfer-fraud precedent already used at `us_finance_bec`. Simulated losses
  at seed 42: AVG AUD 125,110 → 154,815, P99 550,725 → 664,247.
- Scouted and rejected: Levitas Capital would have matched sector and size, but no
  primary document states its loss and the reported figures diverge across secondary
  coverage. A law-enforcement primary source with one unambiguous figure wins.
- The family stays ADR-0007 `mixed`, which is the point — the fix was
  construct-appropriateness, not coherence.

### Honesty machinery
- The strength ledger records the **ADR-0007 coherence split** (`families_coherent`
  / `families_mixed`), folded in at the cut exactly as the ADR-0003 population split
  was at v0.2.0. The first entry carrying it reads *newly measured*, never a
  fabricated "+4" against entries that never counted families — pinned by a test
  verified to fail when the guard is removed.
- README front door carries the third axis: a maximum here is *the largest loss we
  found*, never *the largest loss that can happen*.
- ADR-0007 was missing from the ADR index; both it and ADR-0008 are now listed.

## v0.4.0 — 2026-08-03

The finished map. Since v0.3.0 every remaining viable cross-country bridge was
retired, and every bridge still standing now carries either a recorded
structural-negative scout (the source does not exist publicly) or a deliberate
methodological note. Further cross-country reduction requires new data to be
published, not found.

Data-pack release: `data_pack_releases/2026.08.03-v0.4.0.json`.
Ledger tick since v0.3.0: **cross-country bridges 20 → 15**; labels now carry
**zero label/gate mismatches** for the first time.

### Japan: frequency moves to Japanese readings
- 0.51 (2024 survey, n=500) and 0.58 (2023 survey, n=300) replace the global
  manufacturing rates, from the same Wayback-pinned Sophos editions as the
  Australian rework. The recorded doubt about whether the survey sampled Japan
  is settled. The shard meets the gate's country-relevance minimum and is
  promoted to `benchmark_review_candidate`.

### Australia data breach: typical loss moves to IBM's Australian financial-services cell
- AUD 6.31M (IBM 2026 Australian industry cut, via verified secondary coverage
  because IBM gates the report) replaces the converted global average at nearly
  the same value — the country and industry dimensions stop being bridged. The
  shard clears the gate and its label is earned rather than over-claimed.

### Singapore: frequency floor and ceiling move to Singapore anchors
- Floor 0.001 (SPF's 377 reported BEC cases over SingStat's 371,000
  enterprises — the revision the old US-derived record asked for) and ceiling
  0.80 (CSA's all-cyber organisation prevalence, deliberately threat-bridged)
  replace the two US frequency bridges.

### Honesty machinery
- **Superseded records are now deleted, not kept as alternatives:** the public
  provenance card selects by confidence-then-id, not calibration selection, so
  a kept non-selected record made the card display evidence the simulation did
  not use. Found, fixed, and recorded in the revisions log.
- The last eight legacy `estimated` placeholder records across SG and AU were
  removed; documented alternatives live in the calibration rationales.
- US data breach promoted to `benchmark_review_candidate` (it had been
  under-labeled against a passing gate — under-claiming is also drift).

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
