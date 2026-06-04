# Contributing To RiskShard Content

RiskShard content should grow through reviewed source, extraction, evidence, and calibration files. Do not add new product surface area to support a content contribution.

## Source Registry Checklist

- Add public sources to `sources/registry.yaml`.
- Include `id`, `title`, `publisher`, `source_type`, `url`, `publication_date`, `access_mode`, `intended_use`, and `usage_notes`.
- Use `fallback_urls` when the landing page links to a more stable PDF or CSV artifact.
- Run `python scripts/gather_sources.py`.
- Commit `sources/manifest.json`, not files under `sources/raw/`.

## Extraction Checklist

- Add reviewed facts to `extractions/`.
- Keep extraction records close to the source wording.
- Link each extraction to a `source_id` from `sources/manifest.json`.
- Mark contextual-only facts explicitly when they are not suitable as scenario parameters.

## Evidence Checklist

- Add normalized records to `evidence/`.
- Keep evidence separate from simulation-ready scenarios.
- Use `source_backed`, `estimated`, or `synthetic` honestly.
- Source-backed evidence must include `source_id` and `citation_detail`.
- Estimated or synthetic records must explain limitations and normalization assumptions.
- Use taxonomy IDs from `taxonomies/`.

## Calibration Checklist

- Add calibration profiles to `calibrations/`.
- Keep scenario ranges in the simple `frequency.min/likely/max` and `impact.min/likely/max` shape.
- Keep FX assumptions in `calibrations/fx_rates.yaml`.
- Use `scripts/update_fx_rates.py` when FX rates need refresh.
- Run calibration with both JSON and Markdown output for review.

## Review Commands

```bash
python scripts/gather_sources.py
python scripts/validate_evidence.py
python scripts/calibrate_scenario.py scenarios/au_finance_ransomware_midmarket.yaml \
  --org-profile org_profiles/au_finance_midmarket.yaml \
  --evidence evidence \
  --calibration calibrations/au_finance_ransomware.yaml \
  --threat ransomware \
  --report-output results/au_finance_ransomware_calibration.json \
  --markdown-output results/au_finance_ransomware_calibration.md \
  --scenario-output results/au_finance_ransomware_calibrated.yaml
python -m unittest discover -s tests
```

Generated files in `results/` are local review artifacts unless they are intentionally promoted as documented examples.
