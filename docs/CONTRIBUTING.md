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

## Risk Module Checklist

- Add a module descriptor to `risk_modules/` when a scenario is intended to be practitioner-facing.
- Link the scenario, default org profile, calibration profile, evidence files, reviewed extractions, and any control profiles.
- Include `good_for` and `not_good_for` practitioner notes.
- Keep module descriptors as catalog metadata; do not move evidence into the module file.
- Run `python scripts/riskshard_modules.py packs <module-id>` and `python scripts/riskshard_modules.py propose <module-id>`.

## Country Pack Checklist

- Start with `python scripts/riskshard_modules.py countries`.
- Pick a country where you can review local sources in context.
- Prefer the recommended first module unless you have stronger local evidence for another threat.
- Add sources, reviewed extractions, evidence, calibration, and module metadata together.
- Keep translations and source limitations visible when sources are not in English.
- Before opening a pull request, run `python scripts/contributor_preflight.py path/to/proposed_pack`.

## Proposed Pack Layout

Contributor preflight accepts a proposed pack directory with the same relative
paths used by the main repo:

```text
sources/registry.yaml
evidence/*.yaml
extractions/*.yaml
calibrations/*.yaml
risk_modules/*.yaml
scenarios/*.yaml
org_profiles/*.yaml
README.md
```

The risk module should reference artifacts by their eventual repo-relative
paths. Preflight will accept files that already exist in the repo or files that
exist inside the proposed pack at those paths.

## Review Commands

```bash
python scripts/gather_sources.py
python scripts/validate_evidence.py
python scripts/riskshard_modules.py list
python scripts/riskshard_modules.py countries
python scripts/riskshard_modules.py packs au_finance_ransomware_midmarket
python scripts/riskshard_modules.py propose au_finance_ransomware_midmarket
python scripts/contributor_preflight.py path/to/proposed_pack
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
