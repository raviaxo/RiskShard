# EDGAR cyber-loss corpus census — sizing the ADR-0005 registry decision

*Internal working doc (governed by [`../../AGENTS.md`](../../AGENTS.md)). Produced 2026-08-13 to
answer one question with a number instead of an argument: **is the publicly-filed cyber loss
corpus dozens or hundreds?** The queue owner is [`NEXT_STEPS.md`](NEXT_STEPS.md); this file is the
measurement behind one of its entries.*

*Reproducible: [`research/edgar_corpus_census.py`](research/edgar_corpus_census.py)
(`discover` → `quantify` → `report`).*

## Why this was measured

[ADR-0005](../adr/0005-documented-loss-event-registry.md) established the feasibility of a
documented loss-event registry and then **Deferred** it (2026-07-31) — explicitly for want of
priority and a second maintainer, not for want of value. Its sample found 4 quantified events in
20 Item 1.05 filers (~27% of those that had filed a later periodic report) and flagged two things
it had *not* measured: how far an Item 1.05 query undercounts, and how many filings ever carry a
number at all.

Two things changed since. [ADR-0010](../adr/0010-where-riskshard-stops.md) made the governed
evidence object the product, which removes ADR-0005's main objection (*"it is a
tail-and-defensibility instrument, it does not solve the mid-market impact gap"* — an objection
that only bites if composing shard distributions is the product). And Adrian Sanabria, asked to
sniff-test the project, independently named the same three sources: **SEC filings, PACER, and
insurance claims-paid reports.**

Twenty-five rows is a blog post. Two hundred is a dataset. The decision turns on which.

## Method

Three discovery lanes, then sentence-level extraction, then a hand verification pass.

| Lane | What it searches | Why |
| --- | --- | --- |
| **A** | Item 1.05 8-K filers, followed to subsequent 10-Q/10-K | The ADR-0005 method, re-run over the whole discovered set rather than 20 filers |
| **B** | 8-K filings mentioning "cybersecurity incident" | Counted, not crawled — a contaminated upper bound whose only job is to size how far Item 1.05 undercounts |
| **C** | 10-K/10-Q matched directly on high-precision **cost phrases** | New here, and the better method |

Lane C is the change that matters. The phrases (`related to the cybersecurity incident`,
`in connection with the ransomware attack`, and seven others) are the connective tissue of a cost
sentence — *"we incurred $X **related to the cybersecurity incident**"* — so a hit is already the
document holding the figure. No 8-K hop is needed, which means it also reaches incidents that
have **no Item 1.05 filing at all**, including those predating the rule's 2023-12-18 effective
date. A bare `"cybersecurity incident"` search over 10-K/10-Q is useless for this: it saturates
EDGAR's 10,000-hit cap on the Item 1C governance boilerplate every 10-K now carries.

Counting is sentence-level throughout — money, incident language and a cost word in the *same*
sentence, the `edgar_verify.py` method. The loose 700-character proximity pass from
`edgar_sample.py` was 50% wrong and is not used to count anything.

**Window:** 2023-01-01 to 2026-08-13. **Cap:** 4 periodic reports per lane-A filer.

## What the machine found

```
A  Item 1.05 8-K:            88 filings, 62 unique filers
B  8-K mentioning the term:  1,400 filings   (contaminated upper bound)
C  periodic-report phrases:  290 documents,  73 issuers

LANE C   290 documents checked · 157 quantified (54%) · 41 distinct issuers
LANE A   62 filers checked · 56 had a later report · 17 quantified
         (27% of filers, 30% of those with a report)
         ADR-0005 comparison: 4/20 filers, ~27% of those with a report

UNION of distinct issuers with ≥1 candidate figure: 50
  found only by lane C, invisible to the ADR-0005 method: 33
```

**Lane A reproduced ADR-0005 almost exactly** — 30% versus ~27% on a sample 3× larger. The
original rate was sound; the original *reach* was not.

## What the hand verification found

**The machine count is not the answer.** Reading one representative sentence per issuer across all
50 candidates: **12 do not survive.**

| Rejected | Why |
| --- | --- |
| Capital One | matched an adjusted-operating-efficiency table, not an incident |
| Cadre Holdings | the $60.4M is segment cost of goods sold |
| Coupang | matched a net-revenue-per-active-customer metric table |
| Enzo Biochem | the fees are Asset Purchase related |
| Prosper Marketplace | software/subscription and professional services growth costs |
| SIFCO Industries | `$3,000` is the **cybersecurity insurance coverage limit**, not a loss — and it is denominated in thousands |
| AFLAC · Halliburton · Mativ | real incident costs, but **bundled** into a larger charge (severance, impairment, merger costs) and not isolable from the disclosed figure |
| CareCloud | costs described, no amount in the sentence |
| Fortress Biotech | a court-ordered recovery of stolen funds, amount not in the matched sentence |
| Sinclair, Inc. | duplicate entity — same $63M as Sinclair Broadcast Group, post-reorganisation filer |

**38 issuers survive.** Of those, 3 carry only an insurance *recovery* (Campbell's, SolarWinds,
Tenet) and 2 carry a period-over-period *delta* rather than an event total (Fidelity National
Financial, SouthState). So **roughly 33 issuers carry a directly usable event cost or impact.**

### Two extraction hazards, both live

1. **Units.** `$302`, `$179`, `$98`, `$3,000` are financial-statement table figures denominated
   in thousands. Read at face value they are wrong by 1000×. AvidXchange's `$179` is $179,000.
2. **Bundling.** Halliburton's `$116M` pre-tax charge is *"primarily related to severance costs, an
   impairment of assets held for sale, expenses related to a cybersecurity incident"* — a single
   number covering three unrelated things. Third-party reporting puts the cyber portion at ~$35M;
   **the filing does not.** An extractor that takes the number nearest the incident language
   inherits the whole charge.

Both are direct support for ADR-0005's requirement that extraction be **verification-assisted,
never automatic**, and for its requirement that **every amount be typed**.

## The answer: dozens, and the method matters more than the count

**Dozens, not hundreds — about 33–38 issuers.** That is larger than ADR-0005's own projection
(~25–30) but it does not reach dataset scale.

Three findings weigh more than the headline count:

- **The ADR-0005 method could only ever have reached a third of it.** 33 of the 50 candidates —
  and most of the verified ones — are invisible from Item 1.05. Item 1.05 is a poor entry point
  because materiality is asserted at the incident, while the cost lands quarters later in a
  periodic report, sometimes with no 8-K ever filed. Cherry Hill Advisory says the same thing from
  the outside: *"real P&L impact tends to arrive later in quarterly results, not at the initial
  8-K."*
- **The corpus reaches well below large-cap.** Bancorp 34 (~$25,000), Bassett Furniture (~$98k),
  AvidXchange ($179k), Data I/O ($388k), iRhythm ($0.7M) sit alongside Coinbase ($345M) and
  Ardent Health ($74M). Verified figures span roughly **four orders of magnitude**; the median
  explicit-unit figure across all matched sentences is ~$7.9M. ADR-0005 guessed the selection bias
  toward large listed entities was "less absolute than assumed" — that is now measured, and it is
  the ADR's strongest surviving claim.
- **It grows without research cost.** Filings arrive every quarter, and a filed figure never goes
  stale. That is a lower upkeep burden than the calibration profiles already maintained here,
  which drift each time a source publishes a new edition.

For scale: the repo currently holds **141 evidence records across 59 sources**. Thirty-odd
documented loss events would be a material addition and a *different kind* of record — per-company
and per-event rather than aggregate.

## Does someone already do this?

**The filings are well tracked. The amounts are not.**

| Who | What they hold | Amounts? |
| --- | --- | --- |
| [Debevoise Data Blog tracker](https://www.debevoisedatablog.com/2026/05/21/cybersecurity-incident-disclosure-form-8-k-tracker-two-year-update/) | 29 Item 1.05 issuers + 50 Item 8.01 issuers (to 2026-05-21); links, dates, amendments, brief summaries | No |
| [Cherry Hill Advisory](https://www.cherryhilladvisory.com/sec-cybersecurity-disclosure-rule-two-year-review) | 47 mandatory + 31 voluntary filings, Dec 2023 – May 2026 | Selectively quotes ~6 headline figures; explicitly does not systematise cost |
| Wilson Sonsini | Item 1.05 plus voluntary 7.01/8.01 filings | No |

So the differentiator narrows and survives: **not "we found the filings" — "we extracted the
amounts, typed them, and attached provenance."** That distinction must be stated honestly wherever
this is described; claiming to have discovered the corpus would be false.

Commercial loss databases do exist (Advisen holds ~150k cyber loss events; Cyentia's IRIS is built
on it) but they are paywalled and distributed as derivatives — no row is checkable by a reader.
That is the gap, and it is an *openness and provenance* gap, not a discovery one.

## What would change this answer

- **More phrases.** Nine were used. The union curve had not flattened — `"related to the cyber
  incident"` alone added 63 new documents as the sixth phrase. The count is a **floor**.
- **A wider window.** 2023-01-01 onward. Pre-2023 incidents (Sinclair 2021, Hanesbrands 2022) are
  reachable and were caught only because a later filing repeated them.
- **Non-US filings, PACER, regulator penalty registers.** Untouched here. Adrian Sanabria named
  PACER specifically and it is not measured.
- **Table-aware extraction.** Coinbase's `$345,210` sits in a table with its unit in a distant
  header. Prose-first matching reads such figures unreliably.

## Recommendation — and it is the owner's call

This is a Change Control decision under
[`../PUBLISHABLE_REQUIREMENTS.md`](../PUBLISHABLE_REQUIREMENTS.md); it is surfaced, not taken.

The measurement does **not** support "this is a dataset play." It supports something narrower and
more defensible: **~33 verified, checkable, per-company loss records, reachable by a method nobody
else is running, growing quarterly, spanning four orders of magnitude and reaching genuinely small
issuers.**

If it proceeds, three requirements fall directly out of this census and are not negotiable:

1. **Every amount typed** — cost · impact · recovery · delta · settlement. Five of 38 verified
   issuers carry something that is *not* a gross event cost, and mixing them would produce
   nonsense.
2. **Verification-assisted, never automatic.** 12 of 50 machine candidates were wrong, in six
   distinct ways.
3. **Units resolved against the statement header**, not the sentence.

And ADR-0005's honest limits stand unchanged and must be restated wherever this appears:
selection bias toward listed entities, materiality censoring at an unknown threshold, and
provisional figures that settle quarters later. **It cannot produce a central tendency, and it
does not close the mid-market impact gap.** Overselling it as either is precisely the error class
this project exists to refuse.
