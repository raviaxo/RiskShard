# Scenario Fixtures

RiskShard scenarios remain intentionally small: `frequency.min/likely/max` and `impact.min/likely/max`.

## Current Calibrated-Workflow Starters

These are the best first-run shards because they have matching evidence and calibration profiles:

- `au_finance_ransomware_midmarket.yaml`
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
