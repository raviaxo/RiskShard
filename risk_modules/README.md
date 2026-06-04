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
countries GB
modules info gb_finance_data_breach_midmarket
packs gb_finance_data_breach_midmarket
use gb_finance_data_breach_midmarket
propose gb_finance_data_breach_midmarket
calibrate
run
```
