# RiskShard Manifest
**Current Phase:** 3.1 (Portfolio & Hardening)
**Last Sync:** 2026-04-17

## Technical State
- `scripts/fair_calc.py`: v3.1 Engine (Portfolio-aware, Schema-validated).
- `schemas/shard_schema.json`: Active and enforcing YAML structure.
- `scenarios/`: Contains 3 active shards (Ransomware, Insider Threat, Midmarket).

## Immediate Command
- `python scripts/fair_calc.py scenarios/`