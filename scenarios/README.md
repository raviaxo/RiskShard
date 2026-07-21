# Scenario Fixtures

RiskShard scenarios remain intentionally small: `frequency.min/likely/max` and `impact.min/likely/max`. A scenario may optionally add conditional `loss_stages` ([ADR-0001](../docs/adr/0001-loss-chain-scenario-modeling.md)) — up to three downstream loss forms, each gated by its own sourced conditional probability (e.g. a rare regulatory penalty after a breach). See `gb_finance_data_breach_regulatory_chain.yaml` for a worked example.

Each scenario should include `metadata.scenario_stage`:

- `governed_starter`: calibrated workflow starter with matching evidence and calibration profile.
- `demo_fixture`: smoke-test or example fixture that is not decision-ready.

## Current Calibrated-Workflow Starters

These are the best first-run shards because they have matching evidence and calibration profiles:

- `au_finance_ransomware_midmarket.yaml`
- `ca_finance_data_breach_midmarket.yaml`
- `de_industrial_ransomware_midmarket.yaml`
- `fr_finance_data_breach_midmarket.yaml`
- `gb_finance_data_breach_midmarket.yaml`
- `jp_manufacturing_ransomware_midmarket.yaml`
- `sg_finance_bec_midmarket.yaml`
- `us_finance_business_email_compromise.yaml`
- `data_breach.yaml`
- `business_email_compromise.yaml`

Use them with:

```bash
python scripts/readiness_dashboard.py
python scripts/calibrate_scenario.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --evidence evidence \
  --calibration calibrations/au_finance_ransomware.yaml \
  --threat ransomware
```

`calibrated_with_assumptions` means runnable, not benchmark-grade. Inspect warnings, selected evidence, and assumptions before treating any output as decision-ready.

## Legacy Demo Fixtures

The remaining files are useful for CLI smoke tests, portfolio aggregation, and simple examples:

- `ransomware.yaml`
- `fin_ransomware_v1.yaml`
- `saas_ransomware.yaml`
- `saas_ransomware_midmarket.yaml`
- `insider_threat.yaml`

Do not treat these as governed benchmark packs until they have reviewed sources, extraction records, evidence records, and calibration profiles.
