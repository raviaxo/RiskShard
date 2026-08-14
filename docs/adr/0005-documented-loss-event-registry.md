# ADR-0005 — Documented loss-event registry

- **Status:** Deferred (2026-07-31)
- **Date:** 2026-07-29
- **Deciders:** repo owner
- **Why deferred, not rejected:** the sampling below established **feasibility, not
  priority** — those are different things. A ~27% yield is workable, but the registry is a
  permanent curation commitment, it does **not** solve the mid-market impact gap (it is a
  tail-and-defensibility instrument), and with no second maintainer every entry is
  indefinite upkeep for one person. The research is kept intact rather than discarded.
- **Revisit when:** the 2026 DORA edition lands (~June 2027, with automated cost-field
  validation), or a second maintainer exists.
- **Being revisited (2026-08-13):** [ADR-0012](0012-loss-event-registry-bounded-trial.md)
  proposes a bounded trial with a kill criterion, against a full census of the corpus
  ([`../internal/edgar_corpus_census.md`](../internal/edgar_corpus_census.md)). Note the
  second-maintainer condition above is **still unmet** — Adrian Sanabria named the same
  three sources independently but declined to maintain. The status here stays *Deferred*
  unless ADR-0012 is accepted.
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

### The sample, run 2026-07-29

*Reproducible: the scripts are kept in
[`../internal/research/`](../internal/research/README.md).*

Took the first 20 unique Item 1.05 filers, followed each to its subsequent 10-Q/10-K, and
looked for a monetary figure attributable to the incident.

A first pass using proximity (money within ~700 characters of cyber-incident language)
returned **6/20**. That number was wrong: re-checking at sentence level — money, incident
language and a cost word in the *same sentence* — showed two were unrelated text caught by
a loose window. **The verified count is 4.**

| filer | figure | quality |
|---|---|---|
| United Natural Foods | "incremental costs of approximately **$26 million** in the fourth quarter of fiscal 2025 as a result of the Cybersecurity Incident" — split $15M gross profit / $11M opex | excellent |
| Lee Enterprises | "**$10.5 million** in cash flow losses attributable to the cyber incident, which have been submitted for recovery" plus **$3.8M** business-interruption recoveries | excellent — gross *and* net |
| Sonic Automotive | "**$30.0 million** of pre-tax benefit in cyber insurance proceeds related to a cybersecurity incident … provided by CDK Global (the CDK outage)" | recovery, not gross loss |
| Data I/O Corp | "ransomware incident … significant remediation costs of approximately **$388,000**" | small-cap issuer |

**Yield: 4/20 filers overall; 4 of the 15 that had filed any later periodic report (~27%),
five 8-Ks being too recent to have one.** Treat this as a **floor**: the method only read
the first two subsequent reports, only matched prose (not tables), and only recognised
certain phrasings.

Three findings matter more than the rate:

- **The figures are directly usable** — attributable in the filer's own words, quantified,
  and dated.
- **Gross and net are distinguishable in practice.** The ADR worried that insurance
  recoveries would blur the picture; the filings turn out to state both (Lee discloses loss
  *and* recovery; Sonic's $30.0M is explicitly *proceeds*, not loss). The confound is
  visible rather than hidden — but it means every entry must record which side it is.
- **Not exclusively large caps.** Data I/O is a small issuer with a $388k remediation cost.
  The selection bias toward large listed entities is real but less absolute than assumed,
  and the corpus does reach nearer the mid-market than expected.

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

**The sample was run and it supports adoption, narrowly.** A ~27% yield among filers that
have filed a later report — a floor, given the method's limits — over a corpus of at least
92 filings and growing means the registry would hold on the order of dozens of citable,
quantified events now, with more arriving every quarter at no research cost beyond
verification.

Adopt with the narrow first slice: **US-listed Item 1.05 disclosures carrying a quantified
cost, from 2024 onward.** Two requirements fall directly out of the sample:

1. **Every amount must be typed.** Sonic's $30.0M is insurance *proceeds*; Lee's $10.5M is
   a gross loss with $3.8M of recoveries stated separately. An untyped registry would mix
   losses with recoveries and produce nonsense.
2. **Discovery must not rely on Item 1.05 alone**, and the extraction must be
   verification-assisted rather than automatic — the loose first pass was 50% wrong, and
   only sentence-level reading with human confirmation produced trustworthy entries.

Expand to other jurisdictions only once the maintenance path is proven.

Measure it honestly: the count of shards whose `impact.max` cites a registry entry rather
than a bridge, and whether anyone outside the project contributes an entry. If neither moves
within two release cycles, the registry is overhead and should be retired rather than
carried.

**Open questions for the owner:** whether the registry lives in `loss_events/` alongside
`evidence/` or inside it; whether non-cyber operational events (the Iberian blackout, the
TARGET2 outage) belong in scope; and whether regulatory fines are registry entries or stay
loss-chain stage evidence, given they are penalties rather than event losses.
