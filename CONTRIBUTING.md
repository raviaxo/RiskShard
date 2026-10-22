# Contributing to RiskShard

RiskShard is an open, evidence-governed cyber-risk project. Contributions —
especially reviewed public sources that strengthen a shard's parameters — are
welcome.

## Ways in — pick your effort level

You don't need to write an evidence record to contribute. In ascending order of
effort, every one of these is a real contribution and gets credited:

1. **[Request a shard](https://github.com/raviaxo/RiskShard/issues/new?template=request_a_shard.md)** —
   name the country/sector/size/threat cell you need and what for. Zero research
   required. Every request is recorded and published in
   [REQUESTED_SHARDS.md](docs/REQUESTED_SHARDS.md) as the project's demand signal.
   **Read this before you spend the two minutes: shard coverage is frozen at 11
   cells, so a request does not currently produce a shard.**
   [ADR-0016](docs/adr/0016-the-audit-is-the-product.md) part 2 froze it and
   [ADR-0006](docs/adr/0006-depth-over-breadth.md)'s 2026-08-22 amendment
   withdrew demand as grounds to reopen it — a new cell is declined however it
   arrives. Asking is still worth doing, because a recorded request is evidence
   about what this corpus is missing, and two things do reopen breadth: a second
   maintainer, or genuinely per-cell impact evidence. Demand is not one of them.
   Treat it as telling us where the gap is, not as a request that gets filled.
2. **[Improve a number](https://github.com/raviaxo/RiskShard/issues/new?template=improve_a_number.md)** —
   you know a closer or stronger public source for an existing figure. Naming it
   is a complete contribution; we do the extraction and verification, you get
   credited by handle.
3. **[Argue with an open judgment call](docs/OPEN_JUDGMENT_CALLS.md)** — some
   values are decisions, not citations, and each open one names the alternative
   not chosen. Practitioner sense is the only qualification.
4. **[Break a number](https://github.com/raviaxo/RiskShard/discussions/106)** —
   the standing challenge: follow any figure to its cited line and show the
   value, the source, or the caveat is wrong. Confirmed breaks are retracted
   publicly and credited.
5. **Bring a full contribution** — a new source or evidence record that
   strengthens one of the 11 existing shards, through the governed path below.
   **Not a new shard:** coverage is frozen (ADR-0016 part 2), so a new cell is
   declined however complete the pack.

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

- Engineering rules: prefer the standard library, keep `scripts/` thin with
  reusable logic in `engine/`, make the minimal change, and keep diffs scoped and
  coherent. Definition of done: tests pass, `validate_evidence` is clean, and a
  real run of the affected path succeeds.
- **If your record anchors an `impact.max`**, it must also declare an
  `exceedance_basis` — what is known about the value being exceeded
  ([ADR-0008](docs/adr/0008-the-governed-tail.md)). Use `none_known` unless the
  source genuinely supports otherwise; that is the honest answer for most published
  evidence and it is *not* a defect. Claim `observed_rank` only when the source
  states N (then say so in `exceedance_detail` — "rank 1 of N=579"), and
  `modeled_quantile` only when the source publishes an actual percentile. The
  schema rejects a quantile or rank claim with no statement behind it.
- The end-to-end example of taking a source to a passing contribution:
  [`docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md`](docs/GOLDEN_CONTRIBUTOR_EXAMPLE.md).
- The benchmark target / content-pack / preflight workflow:
  [`docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md`](docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md).
- Per-artifact checklists (source registry, extraction, evidence, calibration,
  module, country pack): [`docs/CONTENT_CONTRIBUTION.md`](docs/CONTENT_CONTRIBUTION.md).

## Before you open a pull request

```bash
python -m unittest discover -s tests
python scripts/validate_evidence.py
python scripts/contributor_preflight.py path/to/your_proposed_pack
```

Keep diffs scoped and coherent, standard-library-first, and never weaken claim
discipline: "automated benchmark-ready" is not "benchmark-grade."

## How your contribution is reviewed

Every contribution is reviewed against the same, visible bar:

1. **Source** — is it public, citable, dated, and from a credible publisher?
2. **Honesty** — are values either source-backed or clearly labeled as estimates
   or cross-context bridges? Nothing is dressed up as a local claim.
3. **Gates** — does `contributor_preflight.py` pass, do the tests pass, and are
   the evidence quality gates clean?
4. **Methodology** — does it respect the model's limits and avoid overclaiming
   (see [docs/METHODOLOGY.md](docs/METHODOLOGY.md))?
5. **Craft** — is the diff scoped, and is the DCO sign-off present?

**Our promise on feedback.** A decline is never silent. If a contribution isn't
accepted, you get specific, candid, respectful reasons and — where possible — a
concrete path to make it acceptable. If it is accepted, you are credited in
[CONTRIBUTORS.md](CONTRIBUTORS.md) and your source becomes part of the trail every
future user can audit. Standout contributions may be featured in a monthly Shard
Spotlight. Recognition is not an afterthought here — it is how an open, auditable
risk library gets built: one reviewed source at a time.
