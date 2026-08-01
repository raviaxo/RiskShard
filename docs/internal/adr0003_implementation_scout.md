# ADR-0003 parts 1–2 — implementation scout (2026-08-01)

Work started and deliberately checkpointed: the classification pass surfaced a semantic
fork that sets the public headline number, and it should be decided at the top of a
session, not the tail of one. Nothing here is built; this note carries the analysis so
the next session starts warm.

## What was established

**Scale.** 150 evidence records across 15 files. `riskshard_*` starter records
(`source_id: none`, `evidence_type: estimated`) have no source population, so the new
field should be **required only for `evidence_type: source_backed`** records
(JSON-schema `if/then`).

**The engine already sees half the problem.** `engine/evidence.py::score_record`
scores each applicability dimension `exact` vs `fallback` — a record declaring
`countries: [global]` consumed by a US shard is *visibly* borrowed. The invisible case
the ADR targets is the opposite: records whose declared applicability was **narrowed
to the cell while the source population is foreign** (`ic3_census_..._sg_context`
declares `C=[SG, global]` over US-measured data).

**A third case breaks a one-layer design.** `ibm_uk_2025_..._au_bridge` honestly
declares `C=[GB]` — and is consumed by the AU shard anyway, because calibrations
resolve records **by `evidence_id`, bypassing applicability matching entirely**. So a
field relative to the record's own applicability cannot, alone, answer "is this card
cell-matched for this shard?"

## Proposed design (two layers)

1. **Stored on the record** (part 1): `population_match` describing the *source
   population* relative to the record's declared applicability —
   `{status: matched|bridged, bridged_on: [country|sector|size|threat]}`. This is a
   fact about the record, stable regardless of who consumes it.
2. **Computed per card** (part 2): in `engine/provenance.py`, final cell-match =
   record `bridged_on` ∪ dimensions where the record's applicability does not exactly
   contain the shard's cell value (reusing `score_record`'s exact/fallback logic, plus
   "declared-foreign" for the calibration-bypass case). Totals then split
   `params_source_backed` into cell-matched vs bridged, with per-dimension detail.

## The fork that needs an owner decision

What counts as "bridged" in the headline:

- **(a) Cross-country only** — the ADR's motivating case (IC3→SG, Cyentia→CA).
  Bridged ≈ **10–14** of 66. Sharpest signal, understates sector/threat dilution.
- **(b) Any cross-cell dimension** — strict reading of "the shard's own cell". ABS
  all-industry→finance-cell, all-cyber→BEC, cross-cyber→ransomware all count.
  Bridged ≈ **25+** of 66. Honest and much larger than the 6–7 the ADR predicted
  (that prediction was measured on impact parameters only).
- **The rule-breaking case either way:** min/max anchors deliberately drawn from
  adjacent size classes of the *same* country survey (UK large-business 69% as the GB
  stress max; ACCC small-business floors). That is the range-anchoring *method*, not
  borrowing — a mechanical "population ≠ declared" rule flags it as bridged, which
  would misrepresent the method as a defect. Any rule adopted must state explicitly
  how same-survey adjacent-band anchors are treated.

**Recommendation to decide next session:** full-cell strict count as the stored truth,
headline formatted as "X cell-matched · Y bridged, of which Z cross-country" — keeps
the ADR's sharpest signal visible inside the honest total. Same-survey adjacent-band
anchors: propose matched-with-caveat (they are the method), with the size dimension
recorded in `bridged_on` only when the source is a *different* survey/population.

## Surfaces the implementation touches (mapped)

- `schemas/evidence_record_schema.json` — conditional required field
- `engine/evidence_quality.py` — consistency rule (bridged ⇒ non-empty `bridged_on`)
- `engine/provenance.py` — card fields + split totals (note: existing totals key
  `params_bridged` already means resolved-but-not-source-backed; the new counters need
  distinct names, e.g. `params_cell_matched` / `params_cross_cell`)
- `engine/coverage.py`, `scripts/riskshard_modules.py coverage` — report both numbers
- `engine/strength_ledger.py` — new snapshot fields (old entries lack them; render "—")
- `scripts/explorer_template.html` + `build_explorer.py` — status column shows the
  bridge (e.g. "bridged · country"); cover facts split
- `docs/EVIDENCE_REPORT.md` regeneration; `revisions/` entry for the headline change
- Tests: schema requirement, split totals, explorer rendering; existing snapshots

## Draft per-record classification (partial, worksheet at
`scratchpad/classify_worksheet.txt` regenerable via the same script)

Clear bridged-by-declaration (narrowed-to-cell over foreign population):
`ic3_census_global_bec_reported_complaint_rate_floor_sg_context` [country],
`afp_2025_bec_org_prevalence_frequency_likely_sg_context` [country],
`afp_2026_bec_org_prevalence_frequency_stress_sg_context` [country],
`verizon_dbir_2026_bec_median_loss_impact_floor_sg_context` [country],
`cyentia_iris_2022_typical_cyber_event_loss_usd_ca_context` [country, threat],
`cyentia_iris_2025_extreme_security_incident_loss_usd_ca_context` [country, threat],
`cyentia_iris_2022_top5_cyber_event_loss_usd_au_ransomware_context` [country, sector,
size, threat], `ibm_cost_data_breach_2025_global_average_cost_usd_ca_context`
[country], `sophos_fin_services_ransomware_frequency_stress_2024` [country],
`us_finance_breach_frequency_{min,likely,max}_uk_bridge` [country],
`uk_dsit_2026_medium_business_breach_prevalence_au_bridge` [country],
`uk_dsit_2026_large_business_breach_prevalence_au_stress_bridge` [country, size],
`fbi_ic3_2025_bec_{average_loss,complaints,adjusted_losses}` (declared global over US
complainant population) [country], `verizon_dbir_2026_median_payment_fraud_impact_floor_ai_fraud`
[country, threat], `ibm_uk_2025_financial_services_breach_average_cost_gbp_au_bridge`
(declared-foreign: matched on its own declaration, bridged at AU card level).

Cross-threat dilution (decide under the fork): `abs_2025_au_business_cyber_incident_
prevalence_frequency_likely` [sector, size, threat], `myob_2024_...` [threat],
`business_qld_...` (both shards) [threat], `asteres_fr_cyberattack_cost_2022` [threat],
`opc_cira_ca_*` [sector, size], `ponemon_2023_*` (global insider, top-risk cell) —
plus the Cyentia records that declare only global/all (matched at record level,
fallback-bridged at card level).

Clear matched: all `uk_dsit` GB-declared records, `eurostat_fr_*`, `cesin_fr`,
`ibm_france`, `gdpr_article_83`, `fca_equifax`, `bitkom_de_*`, `sophos_manufacturing_*`
(declared global/manufacturing), `npa_jp_*`, `oaic_*`, `abs_au_active_businesses`,
`spf_*` (SG-declared for SG), `netdiligence US FS SME` records, `coalition`, `afp US`
records for the US shard, `gartner/regula` deepfake, `arup` (documented-case anchor),
`accc_abs_au_small_business_scam_loss_report_rate_floor_2025` (same-survey small-band
floor — the adjacent-band question).
