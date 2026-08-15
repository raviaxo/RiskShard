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

*Findings 1–4 and 6–7 derived 2026-08-13 against data pack `22db117f2bec`; finding 5 derived
2026-08-14 against data pack `fe0d0ffab227`. Counts move as evidence changes; the tools are the
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
if a source published one, and no source consulted does. NetDiligence 2025 and Verizon DBIR 2026
were checked directly for this and neither publishes one.

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
| `impact.max` anchors carrying an exceedance statement | **2 of 11** |
| carrying **none** (`none_known`) | **7 of 11** |
| shards taking most of their modeled loss from the maximum alone | **7 of 11** |

Seven maxima say *a loss this size happened*, not *how often a loss is worse*. They are the largest
loss found, not the largest loss possible — and in seven of eleven shards that anchor drives most of
the modeled average. **A figure mostly driven by an anchor that admits no exceedance probability is
a figure resting on one observation.**

The missing thing is a denominator: how often a loss of size X is exceeded, across a known
population. We have not found one, publicly, anywhere — see finding 6.

### 4 — Half our parameters are borrowed from a population we are not modelling

*Derived by [`engine/provenance.py`](../engine/provenance.py) ·
[ADR-0003](adr/0003-shared-impact-bridges.md)*

| | |
| --- | --- |
| parameters traceable to a named public source | **66 of 66** |
| drawn from the shard's own cell | **31 of 66** |
| **bridged** — borrowed across country, sector, size or threat | **35 of 66** |
| of those, borrowed across **country** | **15** |

"100% source-backed" was true and was doing too much work, which is why the headline was split on
2026-08-01. Cell-matched and bridged are different claims and only one of them is strong.

### 5 — No record states the population that was actually measured

*Measured 2026-08-14 · derived by [`engine/provenance.py`](../engine/provenance.py) ·
pinned by [`tests/test_provenance.py`](../tests/test_provenance.py) ·
[ADR-0011](adr/0011-fit-is-a-facet-set.md)*

| | |
| --- | --- |
| records declaring `applicability` | **141 of 141** (required by schema) |
| …that declare a **narrow** value on a facet their own `population_match` says was not measured | **17 of 141** |
| records stating the observed population as a field | **0 of 141** |
| parameters labelled **bridged** on the published surfaces | **35 of 66** |
| …bridged for a reason **intrinsic to the record**, true for every reader | **25 of 35** |
| …bridged **because of our cell** — the only part that moves with your target | **10 of 35** |

[ADR-0011](adr/0011-fit-is-a-facet-set.md) decided that fit must be computed against a stated
target, and that `applicability` — *"the observed population"* — should be surfaced as the
target-independent fact a consumer computes their own distance from. Building that surface is what
found the problem: **`applicability` is not the observed population.** It is the cell a record is
*declared usable in*, which is frequently narrower than what the source measured.

The clearest case is the US BEC frequency floor. It declares
`industries: [financial_services]`, `company_size_bands: [mid_market]` — while its IC3 numerator
and Census SUSB denominator are both economy-wide, which its own
`population_match.bridged_on: [sector, size]` correctly records. Publishing that declaration under
a *measured on* label would have retired one mislabel by shipping another, on 17 records.

So the field is published as **declared for**, the gap gets its own column — **not measured on** —
and the genuinely target-relative part (does this record name *our* country?) is the only thing
labelled as fit. What no column can give you is the observed population itself: **no published
source reports it as a field, and we have not invented one.** It is recoverable only as the gap
between the two declared lines.

Splitting the label produced a second number that is more useful than the one it came from.
[Finding 4](#4--half-our-parameters-are-borrowed-from-a-population-we-are-not-modelling) reports 35
of 66 parameters as *bridged*, and that single flag has been carrying two unlike things. **25 of
those 35 are bridged for a reason intrinsic to the record** — the source measured a broader
population than the record declares — which is equally true for you, for us, and for a reader in a
country none of our shards cover. Only **10 of 35** are bridged because of *our* cell, and those
are the only ones that change when you substitute your own. The headline count of 35 is unchanged
and still correct; what it means is now separable.

This finding cost nothing and moved nothing: all 66 published values, statuses, bases, exceedance
statements, sources and caveats are byte-identical before and after, and all 35 bridged rows keep
every facet they had. Only the labels changed.

---

## About the published data everyone cites

### 6 — A mortality register is not a loss registry

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

### 7 — The SEC loss corpus is real, reachable, and smaller than it looks

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
