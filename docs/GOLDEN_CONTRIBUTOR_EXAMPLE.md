# Golden Contributor Example

This is one complete, accepted contribution, start to finish. Copy its shape when
you strengthen a shard or add evidence. It takes **one public source** and turns
it into a **visible improvement** in a real Risk Shard, ending in a passing
contributor preflight and a short pull-request note.

The worked change: replace the Canada data-breach shard's `impact.likely` anchor —
previously a **global** IBM average converted to CAD via a low-confidence secondary
article — with the **primary IBM Canada** national average breach cost, reported
directly in CAD.

- Shard: `ca_finance_data_breach_midmarket`
- Parameter improved: `impact.likely`
- Before: global IBM average (USD 4.4M) → CAD via FX; Canada figure only available
  through a low-confidence ITPro secondary article.
- After: `impact.likely` = **CA$6,980,000**, direct from the primary IBM Canada
  newsroom release, no FX conversion, Canada-specific.

## The pipeline (every contribution follows this)

```text
sources/registry.yaml  ->  extractions/  ->  evidence/  ->  calibrations/  ->  evidence pack  ->  preflight
```

Nothing becomes a model parameter until it has passed through each stage and been
reviewed. Source-gathering alone never changes a number.

## Step 1 — Register the source

Add the primary source to `sources/registry.yaml`. Keep secondary/news sources
labeled honestly; prefer primary publishers.

```yaml
- id: ibm_canada_cost_data_breach_2025
  title: "IBM Report: Canadians' Data Security Under Increased Threat, While Breach Costs Surge"
  publisher: IBM
  source_type: data_breach_cost_research
  url: "https://canada.newsroom.ibm.com/2025-07-30-IBM-Report-Canadians-Data-Security-..."
  publication_date: "2025-07-30"
  access_mode: public_html
  trust_tier: high
  intended_use: [Canada average breach cost, Canada data breach loss magnitude]
  usage_notes: >
    Primary IBM Canada release. CA$6.98M national average is all-sector and
    enterprise-weighted; treat as an upper-leaning mid-market likely anchor.
```

## Step 2 — Gather it (real bytes, real hash)

```bash
python scripts/gather_sources.py
```

This fetches the URL and records its `sha256`, byte count, and gather timestamp in
`sources/manifest.json`. Raw downloads stay local and Git-ignored; the manifest is
committed. If a source will not fetch in your runtime, mark it inactive rather than
faking a citation.

## Step 3 — Record a reviewed extraction

Add the human-reviewed fact to `extractions/ca_finance_data_breach_reviewed.yaml`.
Extraction captures the exact quote, the value, and — critically — the honest
limitations, before it becomes a model input.

```yaml
- id: ibm_canada_2025_average_breach_cost_cad
  source_id: ibm_canada_cost_data_breach_2025
  citation_detail: Release reports Canadian businesses are losing CA$6.98 million on average to data breaches...
  fact: IBM reported that Canadian businesses lost an average of CA$6.98 million per data breach in 2025...
  value: 6980000
  unit: currency
  currency: CAD
  limitations: All-sector national average, not mid-market- or financial-services-specific; IBM's sample skews larger organizations.
  evidence_record_ids: [ibm_canada_2025_average_breach_cost_cad]
```

## Step 4 — Normalize into an evidence record

Add the simulation-ready record to `evidence/ca_finance_data_breach.yaml`. Set
`evidence_type: source_backed`, a truthful `confidence`, and precise
`applicability`. Confidence reflects **fit to this shard**, not source fame — a
primary source used all-sector for a mid-market shard is `medium`, not `high`.

```yaml
- id: ibm_canada_2025_average_breach_cost_cad
  parameter: impact.likely
  value: 6980000
  currency: CAD
  source_id: ibm_canada_cost_data_breach_2025
  evidence_type: source_backed
  confidence: medium
  applicability: {industries: [all], countries: [CA], company_size_bands: [all], threats: [data_breach]}
```

## Step 5 — Select it in the calibration

Point the parameter at the new record in `calibrations/ca_finance_data_breach.yaml`.
Because the value is already CAD, use `transform: direct` (no FX). Update the
`rationale` and the profile `notes` so the caveat travels with the number.

```yaml
impact:
  likely:
    evidence_id: ibm_canada_2025_average_breach_cost_cad
    transform: direct
    round_to: 10000
    rationale: Primary IBM Canada national average (CA$6.98M, 2025), already in CAD, replacing the global bridge...
```

## Step 6 — Confirm it flows through

```bash
python scripts/validate_evidence.py
python scripts/riskshard_modules.py packs ca_finance_data_breach_midmarket
python scripts/riskshard_modules.py propose ca_finance_data_breach_midmarket
```

Expected: `impact.likely: source_backed best=ibm_canada_2025_average_breach_cost_cad`,
and a calibrated `impact.likely` of **6,980,000 CAD** with zero warnings.

## Step 7 — Pass preflight

```bash
python scripts/contributor_preflight.py
```

Expected: `Status: pass` across source registry, evidence quality, extraction
mappings, contributor docs, and the data-pack fingerprint.

## The pull-request note (three sentences)

> Replaces the Canada data-breach shard's `impact.likely` anchor with the primary
> IBM Canada 2025 national average breach cost (CA$6.98M), gathered from the IBM
> Canada newsroom and recorded as a source-backed evidence record in CAD, removing
> the previous global-bridge + FX assumption and the low-confidence ITPro secondary.
> The figure is an all-sector, enterprise-weighted national average, so it is
> labeled `confidence: medium` and documented as an upper-leaning likely anchor for
> a mid-market shard, with min/max still on global bridges pending Canadian
> evidence. Evidence gates, module preflight, and the full test suite pass.

## What made this contribution acceptable

- A **primary** source replaced a **secondary** one.
- The number moved from a **global bridge** to a **country-specific** anchor.
- The **limitations were made louder**, not quieter — confidence stayed `medium`
  and the enterprise-weighting caveat is recorded everywhere the value appears.
- Every claim is traceable: source -> extraction -> evidence -> calibration.
