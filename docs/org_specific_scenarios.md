# Org-Specific Scenario Workflow

RiskShard no longer applies heuristic contextual multipliers from organization profile fields. Org-specific analysis should be explicit: use an organization profile to select and normalize evidence, write a calibrated scenario, then run the standard simulator against that scenario.

## Recommended Flow

```text
org profile + reviewed evidence + calibration profile
    -> calibrated scenario YAML
    -> Monte Carlo simulation
    -> JSON report / LEC chart
```

## Example

```bash
python scripts/calibrate_scenario.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --evidence evidence \
  --calibration calibrations/au_finance_ransomware.yaml \
  --threat ransomware \
  --report-output results/au_finance_ransomware_calibration.json \
  --markdown-output results/au_finance_ransomware_calibration.md \
  --scenario-output results/au_finance_ransomware_calibrated.yaml

python scripts/fair_calc.py results/au_finance_ransomware_calibrated.yaml \
  --trials 10000 \
  --dist pert \
  --seed 42 \
  --export
```

This keeps the simulation engine simple and makes every org-specific parameter range reviewable in the scenario YAML and calibration report.

## Future Work

Evidence-backed contextual calibration can come back later when there are reviewed evidence records for organization factors such as internet exposure, third-party dependency, data sensitivity, and regulatory intensity. Those adjustments should be source-backed and reported separately from direct frequency or impact evidence.
