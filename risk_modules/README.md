# Risk Modules

Risk modules are the practitioner-facing catalog layer for RiskShard. A module
points to the scenario, organization profile, calibration profile, evidence,
extractions, controls, and source-governance records needed to inspect and run
one risk shard.

They are deliberately small YAML descriptors. The simulation-ready scenario
format stays simple, and evidence remains in `evidence/`.

The intended console pattern is:

```text
modules
modules info au_finance_ransomware_midmarket
packs au_finance_ransomware_midmarket
use au_finance_ransomware_midmarket
propose au_finance_ransomware_midmarket
calibrate
run
```
