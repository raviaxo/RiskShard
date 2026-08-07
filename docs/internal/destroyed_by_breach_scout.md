# Scout — *Destroyed by Breach* (destroyedbybreach.com)

*Assessed 2026-08-07. Surfaced by Ser. Internal working note.*

## What it is

A research index maintained by **Adrian Sanabria** as part of The Defenders Initiative:
every organisation known to have **ceased to exist as a direct result of a cyber incident**.
**35 entities · 12 countries · 2002–2026.** Columns are organisation, industry, location,
"what killed them" (a causal chain, e.g. *loss of customer trust → loss of customers → ran out
of money*), and date. Case studies are advertised but **not yet published**.

Inclusion is strict and stated: the organisation had to *primarily* fail because of the
incident. Sanabria explicitly excludes companies that had an incident and failed anyway, and
is considering a separate "badly hurt by a breach" list.

## Why it exists — and why that matters to us

He built it to check a statistic: *"60% of small businesses will close within six months of a
cyber attack."* He traced it to a single individual who **admitted he did not know where it came
from and kept using it anyway** (debunked by Joseph Marks, Nextgov, 2017). Nearly a decade of
searching produced the opposite conclusion:

> "It is exceedingly rare for cybersecurity attacks to kill companies. It rarely happens more
> than once or twice per year, globally."

That is the same act RiskShard performs structurally — follow a number to its source, find
nothing, say so publicly — done by hand, for one statistic, over a decade. **This is the closest
thing to a peer project the scouting has turned up, and it is not a competitor.**

## Verdict on the three angles

**1. Citable loss source? Not for magnitude — but yes for the tail's *rarity*.**
It publishes **no dollar figures at all** (checked: zero currency mentions across the list and
stories pages). So it does **not** move the impact wall, and it is not an ADR-0005 registry
today. What it does supply is the thing the worked decision just identified as missing:
[`WORKED_DECISION_AU_RANSOMWARE_LIMIT.md`](../WORKED_DECISION_AU_RANSOMWARE_LIMIT.md) shows the
portfolio's `single_documented_event_loss` maxima carry **no exceedance probability**, and that
this drives the PERT mean rather than bounding it. Sanabria's index is a defensible base rate for
the most extreme severity class — total organisational loss — at roughly *one to two per year
globally*. That is a rarity statement, not a magnitude one, and it is exactly the missing half.

**Caution before using it:** the denominator is unstated and effectively unknowable (all
organisations, worldwide), the set is partly crowdsourced, and Sanabria himself flags likely
gaps in non-English-speaking countries. It would be a `reported_case_rate`-flavoured floor at
best, and any use must carry that. Do **not** convert it into a probability without a declared
denominator — that is the same error as the `frequency.min` reported-case ratios already labelled
in the portfolio.

**2. Competitor? No — complementary, and structurally so.** He curates *events*; RiskShard
governs *parameters*. No modelling, no simulation, no evidence schema on his side; no curated
mortality set on ours.

**3. Person / venue? The highest-value contact surfaced this session.** Sanabria is
well-known in the industry (his words: "I quickly became known throughout the cybersecurity
industry for this project"), the site takes public suggestions, and his founding act is a
provenance debunk. Persona fit is near-exact for [[gtm-strategy]]'s tier-1/tier-2.

## The real opportunity

His open question — *"I'm considering adding a 'badly hurt by a breach' list. Let me know if
this is something you'd like to see!"* — **is ADR-0005**
([`../adr/0005-documented-loss-event-registry.md`](../adr/0005-documented-loss-event-registry.md),
**Deferred** for want of a second maintainer). If that list carries quantified losses with
sources, it is the documented-loss-event registry RiskShard deferred building, maintained by
someone who has already done a decade of the curation work.

**Recommended (owner's call, not taken):** answer his open question as a practitioner with a
specific reason — a "badly hurt" list with figures and sources attached would be directly usable
as governed evidence, and RiskShard already has the schema, the provenance layer and the
citation identifiers that such a list would need. Do not pitch; answer the question he asked.

## Attribution, if ever cited

The site specifies its own citation format:

> Sanabria, Adrian. *Destroyed by Breach*. https://destroyedbybreach.com. Accessed 7 August 2026.

Not registered in `sources/manifest.json` — nothing cites it yet, and nothing should until there
is a figure to cite.
