# JP shard — frequency pre-scout (for approve-each-anchor)

*Pre-scouted 2026-07-24. **Not applied** — these are candidates for Ser's per-anchor
approval before any evidence is written. Governs [`../../scenarios/jp_manufacturing_ransomware_midmarket.yaml`](../../scenarios/jp_manufacturing_ransomware_midmarket.yaml).*

## What's bridged today (the 2 params to fix)

| Param | Current value | Status |
|---|---|---|
| `frequency.likely` | 0.25 | assumption_only (starter) |
| `frequency.max` | 0.50 | assumption_only (starter) |

`frequency.min` = 0.10 is already source-backed (Cyentia IRIS, global cross-sector).
The whole impact side is already Sophos-2025 + NPA source-backed. So the fix is
**consistent with the shard's own impact sources**: survey-prevalence from Sophos
manufacturing, **not** the NPA÷census floor (which is a reported-incidence floor
~0.0002, below the existing sourced min — rejected in v1 scope).

## Candidate anchors (survey-prevalence, global manufacturing)

Sophos *State of Ransomware in Manufacturing* — "% of manufacturing orgs hit by
ransomware in the last year": **2022 = 55%, 2023 = 56%, 2024 = 65%.** (The 2025 report
reframed around orgs already hit and does **not** headline a % hit, so the clean
prevalence series ends at the 2024 report.)

| Anchor | Proposed value | Source | Why |
|---|---|---|---|
| `frequency.likely` | **0.56** | Sophos 2023 manufacturing % hit | Representative recent prevalence, mid of the series |
| `frequency.max` | **0.65** | Sophos 2024 manufacturing % hit | Highest observed year = stress/high anchor |
| `frequency.min` | 0.10 (keep) | Cyentia IRIS global | Already source-backed floor |

Alternative: `likely = 0.65` (most recent, 2024) — but then `max` has no clean higher
manufacturing prevalence to cite, so the 0.56/0.65 pair is the defensible bracket.

## Caveats that MUST stay loud (per approve-each-anchor)

1. **Attack-prevalence ≠ loss-event frequency.** Sophos "% hit" counts *attacks*, not
   loss events. The 2025 report shows only ~40% of manufacturing attacks resulted in
   encryption (down from 74%). So these anchors likely **overstate loss-event frequency** —
   Ser's call whether to discount, or caveat and keep. **This is the key decision point.**
2. **Not Japan-specific.** Sophos surveys 17 countries (Americas/EMEA/APAC; Japan not
   confirmed in the sample); global manufacturing, 100–5,000 employees, n=332 (2025 cut).
   Same "not-Japan-specific" caveat family the impact records already carry.
3. **Respondent skew.** Survey of orgs with IT/security leaders may overstate true
   population prevalence.
4. **Rising trend** (55→56→65) — a point estimate hides the year-over-year climb.

## If approved → outcome

Flips JP `assumption-bridged → source-backed` (6/6), moving the strength ledger to
**11/11 shards at 6/6, 0 bridged** (+2 source-backed params, −2 bridged) — the first
real ledger delta. Lands as `governed_starter` (survey bridges, loudly caveated), not
benchmark-grade. Sources to add to `sources/manifest.json`: Sophos manufacturing 2023 &
2024 reports.
