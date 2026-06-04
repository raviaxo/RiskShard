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
countries
modules info us_finance_bec_midmarket
packs us_finance_bec_midmarket
use us_finance_bec_midmarket
propose us_finance_bec_midmarket
calibrate
run
```
