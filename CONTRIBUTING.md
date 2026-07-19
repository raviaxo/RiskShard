# Contributing to RiskShard

RiskShard is an open, evidence-governed cyber-risk project. Contributions —
especially reviewed public sources that strengthen a shard's parameters — are
welcome.

## License and the DCO

RiskShard is licensed under the **GNU Affero General Public License v3.0
(AGPL-3.0)**. Contributions are accepted **inbound = outbound**: what you
contribute is licensed to the project and to everyone under the same AGPL-3.0.
You keep the copyright to your contribution.

We use the **Developer Certificate of Origin (DCO)** instead of a CLA. It is a
lightweight, one-line certification (see <https://developercertificate.org>) that
you have the right to submit your contribution. To certify it, **sign off every
commit**:

```bash
git commit -s        # appends: Signed-off-by: Your Name <your@email>
```

By signing off you assert the DCO: the contribution is yours to give (or is
appropriately licensed) and may be distributed under the project's license.

## What good contributions look like

Every number in RiskShard traces to a reviewed public source or is honestly
labeled as an assumption. Follow the governed path — `sources/ → extractions/ →
evidence/ → calibrations/` — and keep bridges and estimates labeled as such.

- Engineering rules and the definition of done: [`AGENTS.md`](AGENTS.md).
- The end-to-end example of taking a source to a passing contribution:
  [`docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md`](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md).
- The benchmark target / content-pack / preflight workflow:
  [`docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md`](docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md).

## Before you open a pull request

```bash
python -m unittest discover -s tests
python scripts/validate_evidence.py
python scripts/contributor_preflight.py path/to/your_proposed_pack
```

Keep diffs scoped and coherent, standard-library-first, and never weaken claim
discipline: "automated benchmark-ready" is not "benchmark-grade."
