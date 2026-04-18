# RiskShard Manifest (Transition State)
**Version:** 3.2 (The Export Update)
**Status:** Operational & Synced

## Current Engineering Truth
- **Engine:** `fair_calc.py` supports ALE, PERT, Portfolio Aggregation, and JSON Export.
- **Data:** Scenarios are validated against `schemas/shard_schema.json`.
- **Logic:** $ALE = \text{Simulated Frequency} \times \text{Simulated Impact}$ (Monte Carlo).

## Resume Command
- `python scripts/fair_calc.py scenarios/ --export`

## Next Session Goal
- Implement Phase 4: Data libraries for DBIR and Cyentia auto-ingestion.