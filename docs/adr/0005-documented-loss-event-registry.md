# ADR-0005 — Documented loss-event registry

- **Status:** Proposed
- **Date:** 2026-07-29
- **Deciders:** repo owner (records intent and a recommendation only)
- **Related:** [`0004-citable-parameter-identifiers.md`](0004-citable-parameter-identifiers.md),
  [`0003-shared-impact-bridges.md`](0003-shared-impact-bridges.md),
  [`../internal/canonical_reference_thesis.md`](../internal/canonical_reference_thesis.md)

## Context

Impact is the constraint. Frequency evidence became abundant (Eurostat for 35 countries,
DORA for EU financial entities); loss magnitude did not.

**The practice this formalises already exists, ungoverned.** Three shards already use a
single documented incident as their `impact.max`:

| shard | value | documented event |
|---|---|---|
| `sg_finance_bec_midmarket` | USD 6,660,000 | SPF: Singapore investment-banking firm, Sept 2024 |
| `us_finance_bec_midmarket` | USD 6,400,000 | Coalition's largest funds-transfer clawback case |
| `gb_finance_data_breach_midmarket` | GBP 11,164,400 | FCA fine, Equifax Ltd |

Each was hand-researched, each is recorded in a different shape, and none is reusable by
another shard or discoverable by a contributor. Every future tail anchor repeats that work.

Meanwhile a **new public corpus has appeared and nobody curates it openly.** Since December
2023, SEC Form 8-K Item 1.05 has required US-listed companies to disclose material
cybersecurity incidents, and subsequent 10-Q/10-K filings frequently quantify the cost.
Add company annual reports in other jurisdictions, regulator penalty registers, class-action
settlements, and insurance-coverage litigation, and there is a growing body of
**publicly filed, legally consequential, quantified loss figures** — the highest-credibility
impact evidence obtainable without an insurer's book.

## Decision

Create a governed **loss-event registry**: structured records of publicly documented cyber
loss events with quantified financial impact, held to the same evidence discipline as
`evidence/` (named source, exact cited line, caveat, retrieval date) and citable under
ADR-0004.

Shape, per event: entity descriptors (sector, country, size or revenue band, listed
status); event descriptors (date, threat family, short factual description); one or more
**typed amounts** — direct cost, total impact, regulatory fine, settlement, insurance
recovery — each with currency, the period it covers, and whether it is *provisional* or
*final*; and the source with filing type, URL and cited line.

Events feed parameters rather than replacing them: a shard's `impact.max` may cite a
registry entry, which is what the three shards above are already doing informally.

## What this is good for — and what it is not

This must be stated precisely, because the failure mode is using it as though it were a
loss distribution.

**Good for:** the **tail** (`impact.max`), and for **defensibility**. "A company in this
sector disclosed this cost in an SEC filing" is the most persuasive artefact available in a
board or audit conversation, and it is a matter of public record rather than a model output.
That directly serves the *defending* moment identified in the strategy note.

**Not good for:** central tendency, and **not representative of mid-market**. Three biases
make it structurally skewed and no amount of curation removes them:

1. **Selection bias toward large, listed entities.** Only companies with disclosure
   obligations appear. Mid-market private firms — the cell this project models — are almost
   entirely absent.
2. **Materiality censoring.** Only incidents judged *material* are disclosed, so the corpus
   is left-censored at an unknown, entity-dependent threshold. Small and moderate losses are
   invisible by construction.
3. **Provisional and partial figures.** Disclosures routinely report "costs incurred to
   date"; final amounts land quarters later, and insurance recoveries are often unstated,
   so gross and net are easily confused.

Registry entries must therefore be usable as tail anchors with those caveats attached, and
must never be aggregated into an average. Central estimates remain the job of insurance
claims studies and official cost statistics.

## Feasibility — tested, not assumed (2026-07-29)

**EDGAR full-text search is a public, free API and it works.** A query for Item 1.05 8-K
filings returned **92 filings spanning 2024 to 2026**, each with company name, CIK, filing
date and document URL, in machine-readable JSON (HTTP 200; SEC requires only a
contact-identifying `User-Agent`).

So discovery is automatable, and the division of labour matches what the project already
does for source gathering: machine finds candidates, human verifies the cited line.

Two things this test did **not** establish, and they decide whether the registry is worth
maintaining:

1. **How many filings actually carry a number.** The 8-K itself usually describes the
   incident without quantifying it; the cost, if it appears, lands in a later 10-Q or 10-K.
   The proportion that ever gets quantified is **unmeasured**, and if it is small the corpus
   is thin regardless of how many filings exist.
2. **How much is filed under Item 8.01 instead.** Companies can report an incident under
   "Other Events" rather than 1.05 and thereby avoid asserting materiality. An Item 1.05
   query therefore **undercounts** by an unknown margin, and the 92 above is a floor, not a
   census.

Both are answerable with a bounded sampling exercise — take 20 filings, follow each to its
subsequent periodic report, and record how many produce a usable figure. **That sample
should happen before adopting this ADR**, not after.

## Costs and risks

- **Maintenance is the real cost.** A registry that goes stale is worse than none, because
  it implies currency it does not have. This needs either sustained automation or a
  contribution workflow, and the decision should not be taken without one.
- **Accuracy obligations are higher than elsewhere in the repo.** Entries name identifiable
  companies and their losses. Everything is drawn from public filings, so it is factual and
  publishable, but it must stay strictly neutral and quote-accurate — no characterisation,
  no blame, no inference beyond the filing.
- **It does not solve the mid-market impact gap.** Overselling it as such would be the very
  error the project exists to prevent.

## Alternatives considered

- **Keep hand-rolling tail anchors per shard.** Status quo. Works, but repeats the research
  each time, produces inconsistent records, and captures nothing reusable.
- **Rely on insurance claims studies alone** (NetDiligence, Coalition, NAIC). Less biased and
  better for central estimates — and worth doing regardless — but aggregated, so it yields no
  citable individual event for the defending moment.
- **Do nothing until mid-market impact data appears.** Two scouting passes suggest it will
  not.

## Recommendation

**Sample before adopting.** Take 20 of the 92 known Item 1.05 filings, follow each to its
subsequent 10-Q/10-K, and record how many yield a usable, quantified figure. That single
exercise decides this: a high hit rate makes the registry the best available impact
evidence; a low one makes it curation overhead dressed as rigour, and it should be dropped
in favour of insurance claims studies.

If the sample holds up, adopt with a deliberately narrow first slice: **US-listed Item 1.05
disclosures carrying a quantified cost, from 2024 onward**. Bounded corpus, tests the
automation, produces citable tail anchors quickly. Expand to other jurisdictions only once
the maintenance path is proven.

Measure it honestly: the count of shards whose `impact.max` cites a registry entry rather
than a bridge, and whether anyone outside the project contributes an entry. If neither moves
within two release cycles, the registry is overhead and should be retired rather than
carried.

**Open questions for the owner:** whether the registry lives in `loss_events/` alongside
`evidence/` or inside it; whether non-cyber operational events (the Iberian blackout, the
TARGET2 outage) belong in scope; and whether regulatory fines are registry entries or stay
loss-chain stage evidence, given they are penalties rather than event losses.
