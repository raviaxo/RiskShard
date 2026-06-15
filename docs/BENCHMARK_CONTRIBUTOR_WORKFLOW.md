# Benchmark Contributor Workflow

Last updated: 2026-06-15

This is the working path for turning a country, industry, company-size, and
threat idea into a reviewable RiskShard evidence pack.

## 1. Pick A Target

Start with the benchmark roadmap:

```bash
python scripts/benchmark_program.py
python scripts/benchmark_program.py --sprint seeded
python scripts/riskshard_modules.py countries
```

Prefer an existing Benchmark-Grade 30 target unless there is a strong reason to
propose a new one. The target controls the expected country, industry,
company-size, and threat context.

## 2. Build The Pack

A proposed pack should use the repo-relative layout that will be merged:

```text
sources/registry.yaml
evidence/*.yaml
extractions/*.yaml
calibrations/*.yaml
scenarios/*.yaml
org_profiles/*.yaml
risk_modules/*.yaml
README.md
```

Source-backed evidence needs `source_id`, `citation_detail`, publication date,
source URL or citation, and reviewed extraction mapping. Estimated or synthetic
records are allowed only when they are labeled honestly and are not used to
claim benchmark readiness.

## 3. Validate Locally

Run preflight before review:

```bash
python scripts/contributor_preflight.py path/to/proposed_pack
```

For benchmark targets, preflight checks that the proposed risk module maps to
`benchmark_targets/benchmark_grade_30.yaml` and that the module context matches
the target context. A pack can still be useful without a benchmark target, but
that should be an explicit review decision.

## 4. Export Review Evidence

For an existing module, export a portable module evidence-pack artifact:

```bash
python scripts/riskshard_modules.py packs au_finance_ransomware_midmarket \
  --export results/au_finance_ransomware_evidence_pack.json
```

The artifact includes the module evidence-pack summary, file list, SHA-256
hashes, and review commands. It is a local review artifact, not a published
release.

## 5. Acceptance Bar

A shard is only ready for human benchmark review when:

- all six direct parameters are selected;
- selected direct evidence is source-backed;
- selected confidence is medium or high;
- selected source feeds are current;
- selected evidence maps to reviewed extraction records;
- at least two independent selected sources are used;
- country and industry relevance thresholds are met;
- `python -m unittest discover -s tests` passes.

The automated gate says `benchmark_ready`; human reviewers still decide whether
the caveats are acceptable for a release claim.
