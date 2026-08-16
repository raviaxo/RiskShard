# Findings

**What governing published cyber-loss evidence turned up — including about our own numbers.**

This page exists because the point of governing evidence is that it lets you measure your own
defects. Every count below is **derived mechanically** from the repository by a named tool, not
maintained by hand, and every one can be re-run. Where a finding contradicts something this
project previously published, the withdrawal is on this page rather than quietly edited away.

Nothing here says the sources are wrong. Verizon, Cyentia, IBM, NetDiligence and the rest measure
what they say they measure. These findings are about **what happens when you try to use published
figures as model inputs** — and about what this repository was doing with them.

Nothing here says the published outputs are too high or too low, either. A shard describes a
**cell** (country × sector × size × threat), not a company, and within a cell loss varies by orders
of magnitude on dimensions the shard does not model. *"Too high"* has no referent to be measured
against. That claim was made once on this project and withdrawn — see
[Withdrawn claim 1](#withdrawn-claim-1--the-numbers-are-inflated-2026-08-08).

*Findings 1–4 and 7–8 derived 2026-08-13 against data pack `22db117f2bec`; finding 5 derived
2026-08-14 against data pack `fe0d0ffab227`; finding 6 derived 2026-08-15 against data pack
`3b9409a44c6b`. Counts move as evidence changes; the tools are the
authority, not this page, and [`tests/test_findings.py`](../tests/test_findings.py) fails the build
if any count on it drifts.*

---

## About our own model

### 1 — No anchor we hold is a mode, and the schema cannot express one

*Derived by [`engine/slot_roles.py`](../engine/slot_roles.py) · pinned by
[`tests/test_slot_roles.py`](../tests/test_slot_roles.py)*

The engine composes each three-point range as a beta-PERT, whose second parameter is the **mode** —
the most probable single value.

| | |
| --- | --- |
| `impact.likely` anchors that are a calibrated mode | **0 of 11** |
| …that are a published mean or median instead | **8 of 11** |
| shards using a central-tendency figure as the **floor** | **7 of 11** |
| shards doing both | **6 of 11** |

The deeper version is structural: **no value in the 18-entry `measurement_basis` vocabulary denotes
a mode.** Every one names a mean, median, cost component, prevalence, statutory ceiling, single
observation or estimate. So this is not a gap in some shards — the schema could not express a mode
if a source published one.

**How far that goes beyond our own corpus is now measured rather than implied.**
[ADR-0015](adr/0015-the-source-audit.md) audits the 61 registered sources on what they publish,
and a source-level claim counts only when a human has read the stored artifact:

| | |
| --- | --- |
| registered sources **read** | **58 of 72** |
| …publishing a **mode** | **0 of 58** |
| …publishing a **distribution** over loss or frequency | **12 of 58** |
| …publishing an **exceedance** statement | **17 of 58** |
| …that measure a **population** they name | **45 of 58** |
| held only as a landing page, a press release or no artifact — **unanswerable** | **17** |
| readable in principle, not yet read | **2** |

Until this arc that sentence read *"no source consulted does"*, resting on two reads and carrying no
denominator. **Unread is not evidence of absence**, and the audit publishes the gap beside the claim
rather than behind it. Derived by [`engine/source_audit.py`](../engine/source_audit.py) →
`publishable_claim()`.

**The mode claim is holding. Everything around it was wrong.** The reading was expected to confirm
that public sources offer only point statistics. It does not:

- **UK DSIT Cyber Security Breaches Survey 2026 publishes an exceedance statement** — *"the perceived
  cost for the top 5% of cases (95th percentile) … £4,000 for all businesses and micro/small
  businesses, rising to £10,000 for medium/large businesses"* — together with a median and a 25th–75th
  percentile range. That is P(cost > £10,000) = 5% over a named population, split by size band.
- **Sophos State of Ransomware 2024 publishes a bucketed severity histogram** of ransom payments
  (n=1,097), banded from *"Less than $1,000"* to *"$5 million or more"*, whose open top band states
  that **13%** of paid ransoms exceeded $5M.
- **Verizon DBIR 2025 and 2026 both publish loss distributions** — quantile dot plots of loss due to
  ransom payment (n=351 and n=1,494), with the 2024 median ransom stated at $115,000.
- **Cyentia's IRIS studies publish everything except the mode.** IRIS 2025 gives a full loss
  distribution on a log scale with *"Loss percentile"* as an axis, a median incident cost of about
  $600K, and *"more extreme (95th percentile) losses swell to $32 million"*; IRIS 2022 states that
  *"6% actually exceed the organization's yearly income"* over **77,000 events at 35,000
  organizations**, and then advises modellers directly — *"if you're looking to convey what a really
  bad cyber event might cost, we suggest using the 95th percentile value."* It is also the only
  source that visibly reasons about which central measure to use, switching from a geometric mean to
  a median and explaining why — **and it still never publishes a mode.**
- **IBM's *Cost of a Data Breach* publishes no median at all.** In 12,056 words about the cost
  of a breach, the 2026 edition uses "average" 75 times and "median" **zero** times — no
  percentile, no quartile, no "typical". Its only heading containing *"Distribution"* is
  *"Distribution by sample or region"*, the composition of the sample rather than of cost. The
  2025 edition is built the same way. **The most-cited cyber loss figure in the field is a mean
  published without dispersion**, which is a stronger statement of finding 1's problem than
  anything in our own corpus.
- **Singapore Police Force's 2025 brief states one in a single sentence** — *"about 67.1% suffered
  less than $5,000 in losses, while 5.2% of scam cases suffered at least $100,000"* — and **Sophos
  2023** reports that 40% of paying organisations paid $1M or more.
- **FBI IC3 2025 and NetDiligence 2025 publish point statistics only** — an average loss, a maximum,
  and categorical breakdowns of a total. So do the ACCC, OPC, Bitkom, Asterès and ABS releases.

**The one that publishes nothing is not the one you would guess.** IC3, the ACCC and the OPC are
government reporting bodies sitting on the largest loss datasets in their jurisdictions, and they
publish totals and averages. The exceedance statements come from a UK government survey, a
Singapore police brief and two vendor ransomware surveys.

**And a third of what a practitioner cites is not a measurement at all.** Thirteen of the 38 sources
read — statutes, prudential standards, guidance pages, enforcement notices, single-company
disclosures and trade-press articles — measure no population, because they record an event or set
a rule rather than study anyone. That is not a defect in them; it is a fact about what a citation
to them can support. It is also the structural reason a maximum anchored on one company's
disclosure carries no exceedance ([finding 3](#3--most-maxima-bound-nothing)): there is no
population for the loss to be exceeded *within*.

**⚠️ A claim published on this page earlier the same day was wrong, and the correction is the more
useful finding.** It read: *"The most-cited loss figures in this field are gated"* — on the evidence
that 21 of 61 sources were held only as a landing page, every Cyentia IRIS study among them.

**Cyentia IRIS is not gated.** All three studies are a single ungated link from the page we had
stored, and downloading them took under a minute. The corpus held the landing page because the
source registry pointed at the landing page and the gather stored what it was pointed at. **That was
our defect, not the field's**, and it had been sitting in the corpus for months while the shard
programme cited Cyentia as a bridge source. The registry now points at the documents.

What survives is narrower and still worth knowing: **17 of 61 remain held only as a pointer**,
concentrated in IBM's *Cost of a Data Breach* cuts and Sophos's sector reports, whose sites refuse
automated retrieval. Some of the field's most-cited figures are hard to obtain. Not all of the ones
we could not read were among them.

**And the recovered source changed the result.** Cyentia IRIS is the most complete answer in the
corpus to every question the audit asks except the mode — see below.

So the defensible claim is narrower and considerably more interesting than the one we set out to
check: **the shape of the evidence is not the constraint everyone assumes.** Distributions exist,
and at least two sources state exceedance outright. What no source read so far publishes is a
**mode** — the one parameter a beta-PERT actually requires.

⚠️ **And that turns a finding about the field into a finding about us.** Seven of our eleven maxima
declare `exceedance_basis: none_known` ([finding 3](#3--most-maxima-bound-nothing)), including the
GB financial-services data-breach shard — while DSIT, a source **already in this corpus**, publishes
a 95th-percentile cost for UK medium/large businesses. Whether that retires the declaration is a
separate question with its own evidence work; that it was available and unused is recorded here
rather than quietly fixed.

Four of the eight pass *a mean at `min` and a different mean at `likely`* — two central tendencies
ordered by magnitude and then labelled as a floor and a mode.

**This is declared, not corrected.** Manufacturing a mode to fill the slot would invent the most
load-bearing number in the model. What survives is precise: a **specification mismatch** between
what a beta-PERT's second parameter means and what is passed into it.

*This count was published as 7 of 11 and corrected to 8 on 2026-08-12, when every anchor was
resolved to its `measurement_basis` mechanically instead of by eye. The defect was one shard worse
than stated. Two other counts on the same list reproduced exactly, which is what made the outlier
credible.*

### 2 — Not one impact range measures a single quantity

*Derived by [`engine/coherence.py`](../engine/coherence.py) ·
[ADR-0007](adr/0007-construct-coherence.md)*

| | |
| --- | --- |
| parameter families that are **coherent** | **4 of 22** |
| families that are **mixed** — anchors measuring different quantities | **18 of 22** |
| shards carrying at least one mixed family | **11 of 11** |
| **impact** families that are coherent | **0 of 11** |

A *mixed* range composes anchors that are each validly sourced but are not readings of the same
thing — a cost component beneath a total event cost beneath a statutory cap. The range between them
is not a reading of one quantity, so its width is not uncertainty about one quantity.

Population match and measurement basis are independent: a **fully cell-matched parameter can still
sit in a mixed range**. Being about the right companies does not make two figures the same
measurement.

### 3 — Most maxima bound nothing

*Derived by [`engine/exceedance.py`](../engine/exceedance.py) ·
[ADR-0008](adr/0008-the-governed-tail.md)*

| | |
| --- | --- |
| `impact.max` anchors carrying an exceedance statement | **4 of 11** |
| carrying **none** (`none_known`) | **5 of 11** |
| shards taking most of their modeled loss from the maximum alone | **7 of 11** |

**Two of these moved on 2026-08-16, and the mechanism is worth more than the count.** Nothing was
re-measured and no value changed: the DE and JP manufacturing maxima have anchored on a $5,000,000
ransom threshold since they were built, and reading the source properly turned up the share above
it — Sophos states that **18% of 2025 ransom payments were $5 million or more**, placing $5M at the
82nd percentile of a published distribution. The anchor had carried `none_known` because the
original extraction recorded only that "extreme $5M+ cases saw a slight uptick". **The exceedance
was in the source all along; we had not read it.** That is the first time this portfolio has held a
`modeled_quantile`, and ADR-0008's load-bearing claim that none existed is withdrawn accordingly.

Five maxima still say *a loss this size happened*, not *how often a loss is worse*. They are the largest
loss found, not the largest loss possible — and in seven of eleven shards that anchor drives most of
the modeled average. **A figure mostly driven by an anchor that admits no exceedance probability is
a figure resting on one observation.**

The missing thing is a denominator: how often a loss of size X is exceeded, across a known
population. We have not found one, publicly, anywhere — see finding 7.

### 4 — Seven of our sixty-six parameters are drawn from the population they are used for

*Derived by [`engine/provenance.py`](../engine/provenance.py) ·
[ADR-0003](adr/0003-shared-impact-bridges.md) ·
[ADR-0013](adr/0013-fit-is-derived-not-stored.md)*

| | |
| --- | --- |
| parameters traceable to a named public source | **66 of 66** |
| drawn from the shard's own cell | **7 of 66** |
| **bridged** — borrowed across country, sector, size or threat | **59 of 66** |
| of those, borrowed across **country** | **15** |

"100% source-backed" was true and was doing too much work, which is why the headline was split on
2026-08-01. Cell-matched and bridged are different claims and only one of them is strong.

**This finding got substantially worse on 2026-08-15, and the earlier number was the wrong one.**
It read *31 of 66 cell-matched, 35 bridged* — the headline "half our parameters are borrowed" —
until fit stopped being an authored field and became a value computed against the target cell
([ADR-0013](adr/0013-fit-is-derived-not-stored.md), on the evidence of finding 6 below). The old
count rested on a stored field that treated the same wildcard declaration as borrowing 28 times and
as dilution 72 times.

**Only the count moved; no loss figure did.** The parameters, their sources, values and caveats are
unchanged — what changed is that a record measured over all industries now says so on the sector
facet instead of leaving it to the caveat. Read the new number as *this corpus is a set of bridges,
with seven exceptions*, which is what it always was.

### 5 — A fifth of the bridges were declared against the wrong population

*Measured and repaired 2026-08-14 · derived by
[`engine/provenance.py`](../engine/provenance.py) → `unexplained_bridges()` · pinned by
[`tests/test_provenance.py`](../tests/test_provenance.py) ·
[ADR-0011](adr/0011-fit-is-a-facet-set.md)*

| | |
| --- | --- |
| records declaring `applicability` | **142 of 142** (required by schema) |
| …declaring the cell they were borrowed **for** rather than the population measured | **21 of 142** |
| published parameter cards affected | **16 of 66** |
| published figures that moved when all 21 were corrected | **0 of 66** |
| cards still claiming a bridge their own declaration says matches | **0 of 66** |

[ADR-0011](adr/0011-fit-is-a-facet-set.md) decided that fit must be computed against a stated
target, and that `applicability` — *"the observed population"* — should be surfaced as the
target-independent fact a consumer computes their own distance from. Building that surface is what
found the problem: **`applicability` was not the observed population.** On 21 records it named the
cell the record was *borrowed for*.

The clearest case is the US BEC frequency floor, which declared
`industries: [financial_services]`, `company_size_bands: [mid_market]` while its IC3 numerator and
Census SUSB denominator are both economy-wide. Three US data-breach frequencies declared
`countries: [US]` over a **UK** survey. Two Singapore anchors declared `countries: [SG]` over **US**
data. In each case the record's own `limitations` said so in prose while its structured field said
otherwise — and the prose is not what a machine reads.

**The detector is the finding's durable part.** A record *earns* a bridge on a facet by declaring a
population that does not name the consuming cell's value; claiming one while declaring that very
value is a contradiction the repository can check on itself. It catches two shapes — an exact
restatement of the cell, and one hidden beside a wildcard (`[all, data_breach]`, `[SG, global]`) —
and the second shape is why the first count of this defect, 17, was too low by four.

All 21 were corrected the same day. **No published figure moved**: all 66 values, statuses, bases,
exceedance statements, sources and caveats are byte-identical, every portfolio total is unchanged,
and all 11 shards' AVG/P95/P99 are identical to the digit. Calibration profiles name their evidence
explicitly, so correcting a declaration changes what the record *claims*, not what the simulation
*uses*.

**One number did move, and it is the one worth reading.** The benchmark program is the only
consumer that reads `applicability` directly — it counts a parameter as industry-specific when the
record names the target industry. The seeded sprint's blocker count went **19 → 22**, because
`au_finance_bec`, `us_finance_bec` and `sg_finance_bec` had all been **passing the
industry-relevance gate on the false declaration** and now report the gap they always had. A
readiness bar got harder because the data stopped over-claiming, which is the direction a
correction should move. Recorded in
[`revisions/2026-08-14-three-bec-shards-lose-an-industry-relevance-pass-they-had-not-earned.yaml`](../revisions/2026-08-14-three-bec-shards-lose-an-industry-relevance-pass-they-had-not-earned.yaml).

**What the repair exposed is now the open question.** With the declarations honest, every stored
`population_match.bridged_on` reads as *the declared population does not name this cell's value* —
a statement about a record **and a target**, frozen onto the record at authoring time. That is the
shape [ADR-0011](adr/0011-fit-is-a-facet-set.md) forbids. It cannot simply be derived away either:
an `all` declaration is deliberately *dilution* rather than *borrowing*
([ADR-0003](adr/0003-shared-impact-bridges.md)), and only the author can make that call. Whether
the field should carry its target, or be computed per consumer, is a schema decision and is
recorded as open rather than made quietly.

### 6 — The field that recorded how far a number is from our cell disagreed with itself

*Measured and repaired 2026-08-15 · derived by [`engine/provenance.py`](../engine/provenance.py) →
`derivable_bridges()` · pinned by [`tests/test_findings.py`](../tests/test_findings.py) ·
[ADR-0013](adr/0013-fit-is-derived-not-stored.md)*

| | |
| --- | --- |
| cards whose rendered fit equals the fit derivable from their own declaration | **66 of 66** |
| cards where the two **disagree** | **0 of 66** |
| records still carrying the retired stored field | **0 of 141** |

**Before the repair, the first row was 21 of 66.**

Finding 5 repaired `applicability` so that every record declares the population its source
actually measured. That made a second field checkable for the first time: `population_match`,
which recorded the facets — country, sector, size, threat — on which a record was borrowed across
rather than drawn from the shard's own cell.

**Derived, it disagreed with what was stored on two cards in three.** Counted as individual facet
claims rather than cards, the repository stored **43** where the declarations supported **117**.

The disagreement was not a mistake in one direction. Every stored bridge was supported — finding
5's guarantee, holding at 0. The gap was entirely bridges the declarations supported and the
records did not claim, and **almost all of it was one declaration: `[all]`.** A wildcard says the
measurement was taken over everything, so it does not name our sector or our size. Across the
corpus that situation arises 100 times. It was **recorded as a bridge 28 times and not recorded 72
times** — the same declaration, the same facet, the opposite call.

Two records in one file showed it without any interpretation.
[`evidence/au_finance_bec.yaml`](../evidence/au_finance_bec.yaml) holds
`accc_abs_au_small_business_scam_loss_report_rate_floor_2025`, which declared `industries: [all]`
and `company_size_bands: [all]` and stored `status: matched`, and
`abs_2025_au_business_cyber_incident_prevalence_frequency_likely`, which declared the same two
fields the same way and stored `bridged_on: [sector, size, threat]`. Both records' `limitations`
say in prose that the measure is not financial-services-specific and not mid-market-specific. One
put that in the structured field. One did not.

**This was finding 5's defect one field over.** There, the prose said *borrowed* while the
structured field said *matched*, and the prose is not what a machine reads. Here it was the same
contradiction between the same two layers of the same record, in the field
[ADR-0011](adr/0011-fit-is-a-facet-set.md) named as the one that must be relative to a target.
Nothing checked it, so it drifted.

**What had been offered as the reason not to derive this field turned out to be the finding.**
ADR-0011 recorded that fit could not simply be computed, because an `all` declaration is
deliberately *dilution* rather than *borrowing* ([ADR-0003](adr/0003-shared-impact-bridges.md)) and
only the author can make that call. The call is a real one. It was not being made consistently, and
the field could not be read as though it were.

**The repair.** [ADR-0013](adr/0013-fit-is-derived-not-stored.md) retired the stored field. Fit is
now computed against a named target from `applicability` alone, on one strict rule across all four
facets: a record is bridged on a facet when its declared population does not name that facet's
value for the cell being computed against. `population_match` is gone from the schema and from all
141 records, and the schema **refuses** it rather than ignoring it, so a contributor working from an
old example is told rather than left authoring a field nothing reads.

**No published loss figure moved.** All 66 values, sources, caveats, measurement bases and
exceedance statements are unchanged, every portfolio total is unchanged, and all 11 shards'
AVG/P95/P99 are identical to the digit. The field reaches the provenance surfaces and the explorer
and nothing else — not calibration, not coherence, not exceedance, not the simulation.

**Two published counts moved, and they moved louder.** Cards drawn from the shard's own cell went
**31 → 7 of 66** and bridged cards **35 → 59 of 66**; see finding 4, whose headline changed with
them. Cards bridged across **country** did not move at all, because that facet had been computed
this way since ADR-0003 was implemented — which is why it was the one facet where the stored and
derived values already agreed.

**Not all of the gap was drift, and the part that was not is the cost of the fix.**
[ADR-0003](adr/0003-shared-impact-bridges.md) holds that statutory caps, documented single-event
anchors and same-survey adjacent-band anchors are the range-anchoring *method* rather than
borrowing, and are therefore matched. That is a deliberate rule, and **5 of the 24 cards that
flipped are exemptions of exactly that kind** — two statutory penalty caps, one documented
single-event anchor, and two adjacent-band anchors in the FR shard where a small-business and a
large-business band of one survey bracket a mid-market cell. Deriving strictly does not honour it.
Those five now read as bridged on sector and size, and what they actually are is left to
`measurement_basis` to say. It is a real loss of precision on five cards, taken deliberately so the
field means one thing.

---

## About the published data everyone cites

### 7 — A mortality register is not a loss registry

*Measured 2026-08-12 ·
[`docs/internal/destroyed_by_breach_extraction.md`](internal/destroyed_by_breach_extraction.md)*

Adrian Sanabria, who maintains [Destroyed by Breach](https://destroyedbybreach.com), shared the
full dataset on first contact. All 37 entries were run through a loss-record schema.

| | |
| --- | --- |
| entries carrying the cost of the breach **to the company** | **0 of 37** |
| entries containing any currency amount at all | **4 of 37** |
| breach dates that are a month or year coerced to an exact day | **18 of 37** |
| entries citing **no source** | **12 of 37** |

The four amounts each measure something else: a debt owed to a creditor, a court settlement, a
ransom that was **refused**, and a bribe paid **by the attackers**. There is no figure column —
all four sit in free-text prose, so any mechanical read collects numbers that are not losses.

Dates are stored to the day in a uniform format. **15 of 37 fall on the 1st**, and 18 fall on the
1st, 30th or 31st against roughly 4 expected if the days were genuine. Once a month is stored as a
day, the distinction is unrecoverable.

**It answers *which organisations died after a breach* — not *how often a loss of size X is
exceeded*.** Those are different statistics, and conflating them is the error class this project
exists to catch. See [Withdrawn claim 2](#withdrawn-claim-2--the-denominator-premise-2026-08-12).

### 8 — The SEC loss corpus is real, reachable, and smaller than it looks

*Measured 2026-08-13 · [`docs/internal/edgar_corpus_census.md`](internal/edgar_corpus_census.md) ·
re-runnable via [`edgar_corpus_census.py`](internal/research/edgar_corpus_census.py)*

| | |
| --- | --- |
| candidate issuers found with a quantified incident figure | **50** |
| rejected on hand verification | **12** |
| surviving | **38** |
| carrying a directly usable event cost or impact | **~33** |

Twelve failed in six distinct ways — an operating-efficiency table, segment cost of goods sold, a
revenue-per-customer metric, an **insurance coverage limit read as a loss**, charges bundling
severance and impairment with incident cost, and a duplicate post-reorganisation entity.

Two hazards worth naming for anyone attempting the same extraction:

- **Units.** Statement-table figures are denominated in thousands. AvidXchange's `$179` is
  $179,000; SIFCO's `$3,000` is a $3M coverage *limit*, not a loss.
- **Bundling.** Halliburton disclosed a `$116M` pre-tax charge *"primarily related to severance
  costs, an impairment of assets held for sale, expenses related to a cybersecurity incident."*
  Third-party reporting puts the cyber portion near $35M. **The filing does not.**

**Item 1.05 is a poor entry point.** Materiality is asserted at the incident; the cost lands
quarters later in a periodic report, sometimes with no 8-K ever filed. **33 of the 50 are invisible**
to a method that starts from Item 1.05 filings.

Verified figures span roughly **four orders of magnitude** — about $25,000 to $345M, median ~$7.9M —
and reach genuinely small issuers, not only large caps.

The filings themselves are well tracked (Debevoise, Cherry Hill, Wilson Sonsini). **None of those
trackers extracts or types the amounts.** The gap is openness and provenance, not discovery.

---

## What we got wrong

A project that publishes its reasoning has to publish its corrections at the same volume. These are
not footnotes.

### Retracted figures — 2 (2026-08-01)

*[`revisions/2026-08-01-two-published-figures-retracted-after-the-source-sweep.yaml`](../revisions/2026-08-01-two-published-figures-retracted-after-the-source-sweep.yaml)*

Two published figures were withdrawn outright because **they appear in no primary source**.

- An **insider-misuse frequency pair (66% / 76%)** that circulates widely in survey summaries. The
  76% turned out to be a different vendor measuring a different construct. Replaced with what the
  survey family's artifacts actually say.
- An **AI-enabled-fraud impact figure (~USD 500k)** that was not on the page it cited. Reattributed
  to the report that does contain a figure, at USD 450,000.

Both entered through survey-summary telephone: secondary write-ups quoting each other until the
number detached from any artifact. That is precisely the failure the governed source manifest
exists to prevent, and it happened here anyway. The sweep that caught it now runs against archived
artifacts with verified hashes.

### Withdrawn claim 1 — "the numbers are inflated" (2026-08-08)

An earlier internal note stated that every defect found that week inflated the published numbers and
that the portfolio was very likely overstating loss. **That claim was wrong and is withdrawn.**

It presumes a true value to be high *relative to*, and no such observable target exists. A shard
describes a cell, not a company; within that cell, loss varies by orders of magnitude on dimensions
the shard does not model at all. Direction-of-error language must not reappear without an observable
target to compare against.

*The error class is the one this repo exists to catch: a valid measurement had a directional
conclusion attached that it did not support. The measurement was fine; the inference was not.*

### Withdrawn claim 2 — the denominator premise (2026-08-12)

This project asserted — **in writing, to the dataset's maintainer, before measuring it** — that a
documented loss-event registry such as Destroyed by Breach would supply the exceedance denominator
our seven undeclared maxima lack.

Measurement showed it does not: **0 of 37 entries carry a breach cost.** The premise was right in
general and wrong about this dataset in particular. Recorded here because it was asserted before it
was checked, which is the part worth remembering.

### Framings retired

- **"Metasploit for risk — a vetted module library"** (2026-08-11). The analogy's load-bearing claim
  was portability: take the module, know your target conditions, run it. For a risk observation the
  target conditions *are* the estimand, so nothing travels intact. Retired publicly by the person who
  proposed it publicly — [ADR-0010](adr/0010-where-riskshard-stops.md).
- **"The parameter is the product"** (2026-08-13). Same objection, quieter: the word *parameter*
  smuggles portability back in after it had just been disowned. The governed evidence object is the
  product; a parameter is what exists downstream once a consumer applies local context —
  [ADR-0011](adr/0011-fit-is-a-facet-set.md).

---

## How to break one of these

Every count above is derived by a named tool over data in this repository. If one is wrong, that is
a finding about us and we would rather have it:

```bash
python -m unittest discover -s tests        # the counts are pinned by tests
python scripts/riskshard_modules.py provenance --all --report -   # every number, source, caveat
python docs/internal/research/edgar_corpus_census.py report       # the SEC census
```

Or [open an issue](https://github.com/raviaxo/RiskShard/issues/new) naming the figure, the source,
and the line that contradicts it. A challenge that breaks a number is credited by handle in the
correction record.
