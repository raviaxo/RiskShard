# Open judgment calls

Not every number is a citation; some are decisions. This page lists the judgment
calls currently carried in the dataset that a reasonable practitioner could argue
with — no source-hunting required, just domain sense. Each one names the documented
alternative that was *not* chosen. Disagreeing with one of these **counts as a
contribution**: open the dispute link on the row, or reply in the
[Break a number](https://github.com/raviaxo/RiskShard/discussions/106) thread.

*Maintained by hand at each release; decisions and alternatives also live on the
evidence records themselves.*

| # | Call | The decision | The documented alternative | Row |
|---|---|---|---|---|
| 1 | Australia ransomware stress frequency | 0.70 — the adjacent-year (2023) Australian reading of a steeply declining survey series | 0.80 (the 2022 reading): harsher, but three cycles stale | [frequency.max](https://raviaxo.github.io/RiskShard/#au_finance_ransomware_midmarket/frequency.max) |
| 2 | Australia ransomware stress loss | Latitude Financial's ASX-disclosed AUD 76M — a documented extortion loss at an enterprise-scale lender, used as a deliberate ceiling with size and threat bridged | Cyentia's global top-5% cyber-event loss (USD 52M): a percentile, but global and all-cyber | [impact.max](https://raviaxo.github.io/RiskShard/#au_finance_ransomware_midmarket/impact.max) |
| 3 | Japan ransomware stress frequency | 0.58 — the adjacent-year (2023) Japanese reading, declining series | 0.61 (the 2022 reading) | [frequency.max](https://raviaxo.github.io/RiskShard/#jp_manufacturing_ransomware_midmarket/frequency.max) |
| 4 | Canada breach-loss floor and ceiling | NetDiligence Canadian insured-claims cells at N=8 (floor) and N=84 (ceiling) — thin but country-resident | Cyentia global all-cyber benchmarks: fatter samples, two borrowed dimensions | [impact.min](https://raviaxo.github.io/RiskShard/#ca_finance_data_breach_midmarket/impact.min) |
| 5 | Canada stress frequency | StatCan's 2021 cell (0.273), which carries quality code C ("use with caution") | The adjacent large-band 2023 cell (0.239, quality B) | [frequency.max](https://raviaxo.github.io/RiskShard/#ca_finance_data_breach_midmarket/frequency.max) |
| 6 | Australia data-breach typical loss | IBM's Australian financial-services average (AUD 6.31M) — the exact cell, but IBM publishes no per-cell sample size | IBM's global average (USD 4.44M): broad but fat-sampled | [impact.likely](https://raviaxo.github.io/RiskShard/#au_finance_data_breach_midmarket/impact.likely) |
| 7 | Singapore BEC stress frequency | CSA's all-cyber "over 8 in 10" as a threat-bridged ceiling (0.80) — Singapore-resident but not BEC-specific | AFP's US payments-fraud prevalence (0.74): threat-closer, country-foreign | [frequency.max](https://raviaxo.github.io/RiskShard/#sg_finance_bec_midmarket/frequency.max) |
| 8 | GB breach frequency stays on a survey, not the regulator's case count | UK DSIT survey prevalence (0.43/0.65/0.69), all-industry and therefore bridged on sector | The ICO's own finance-sector cyber case count (357/yr): sector-specific and country-specific, but a reported incidence rather than a prevalence — it implies ~0.6% against a 43% floor, so it measures a different quantity ([assessment](internal/ico_frequency_assessment.md)) | [frequency.min](https://raviaxo.github.io/RiskShard/#gb_finance_data_breach_midmarket/frequency.min) |

The pattern behind most of these: **when local-but-broader and foreign-but-closer
both exist, which one serves a reader better?** The house has leaned local with the
distance declared. If your practice says otherwise for a specific call, argue it —
that's exactly the review these numbers are waiting for.
