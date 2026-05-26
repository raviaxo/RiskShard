# Source Baseline

RiskShard keeps source gathering separate from benchmark extraction.

- `registry.yaml` is the curated list of source materials the project is allowed to gather.
- `manifest.json` is the generated audit trail for the latest gather run.
- `raw/` contains downloaded source artifacts and is ignored by Git.

Run:

```bash
python scripts/gather_sources.py
```

The manifest records each source's publication date, gather timestamp, final URL, HTTP status, content type, byte count, SHA-256 hash, raw artifact path, and any fetch error.

Do not turn a report into a scenario parameter just because it was fetched successfully. Extracted facts should become separate evidence records under `evidence/`, with applicability, confidence, evidence type, limitations, and citation notes.
