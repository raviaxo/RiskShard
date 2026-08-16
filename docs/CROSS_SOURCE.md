# The same question, asked of seven countries by one survey

**How much of a cyber-loss figure is the phenomenon, and how much is the country you
happened to look up?**

*Read 2026-08-16 from the seven country cuts of Sophos's State of Ransomware 2026, each
verified against its stored artifact and recorded in
[`sources/audit.yaml`](../sources/audit.yaml). Every figure below is that source's, not
ours — this page compares published figures, it does not derive new ones.*

## Why these seven are comparable when national surveys usually are not

The hardest problem in reading public cyber-loss evidence is that two figures for "the
same" quantity are almost never measured the same way. Different years, different sample
frames, different size bands, different definitions of loss.

These seven are the exception, and it is worth being precise about why:

- **one instrument** — the same questionnaire, commissioned by one vendor
- **one period** — fielded January to March 2026
- **one size band** — organizations with **100–5,000 employees**, everywhere
- **one currency** — all financial data points in U.S. dollars
- **one denominator** — organizations that were **hit by ransomware in the prior 12
  months**, not all organizations
- **one exclusion, stated** — outlier ransoms of **$40 million or more removed** before
  publication

Method is held constant. What varies is the country.

## What varies when only the country varies

| country | n | median ransom demand | median ransom payment | demands ≥ $1M | mean recovery cost *(excl. ransom)* |
| --- | ---: | ---: | ---: | ---: | ---: |
| **United Kingdom** | 120 | **$2.5M** | — | **65%** | $1.49M |
| **Japan** | 152 | $1.75M | **$3M** | 61% | $1.88M |
| **Australia** | 119 | $1.34M | $855K | 49% | $1.66M |
| **United States** | 377 | — | $1M | 55% | $2.5M |
| **France** | 129 | $500K | — | 39% | $2.02M |
| **Germany** | 139 | $400K | — | 45% | $1.42M |
| **Singapore** | 33 | — | — | — | $1.14M |

*Dashes are figures the source does not publish, not figures we failed to find. Sophos
reports no ransom demand or payment level for Singapore at all; with n=33 that reads as
small-sample suppression rather than omission.*

## The finding

**Median ransom demand spans roughly six-fold across countries — $400,000 in Germany to
$2.5 million in the United Kingdom — on identical methodology.** The probability that a
demand exceeds $1M runs from 39% in France to 65% in the UK.

Three things follow, and the third is the one that matters.

**1. Country is not a detail.** A practitioner who reads "the median ransom demand is
$2.5M" from the UK cut and applies it to a German organization is wrong by a factor of six,
and nothing in the sentence warns them. The figure is correct and the transfer is not.

**2. The ordering does not survive the change of quantity.** The UK has the highest demand
and one of the *lowest* recovery costs; the US has the lowest published median payment and
the *highest* recovery cost. **A country is not simply "expensive" or "cheap"** — which
means a single national multiplier, the intuitive fix, does not work either.

**3. Year-on-year movement is larger than the between-country spread.** Australia's median
demand moved from $217,000 to $1.34 million in one year, and its median payment from
$186,000 to $855,000 — a six-fold jump. Japan's median payment went $525,000 → $3 million.
The UK's demand *fell* 53%. **A figure's vintage matters at least as much as its
geography**, and a two-year-old number is not a slightly stale version of today's — it may
be a different order of magnitude.

## What this page is evidence for

This project's position is that public cyber-loss evidence is **not portable**: an
organization's context is part of the thing being estimated, so a figure measured elsewhere
does not transfer intact ([ADR-0010](adr/0010-where-riskshard-stops.md)).

That is usually argued. **Here it is measured**, and measured under the strongest possible
conditions for the opposite conclusion — same instrument, same quarter, same size band,
same currency, same denominator. Every methodological reason for two figures to differ has
been removed, and a six-fold spread remains.

**That spread is the portability claim, quantified.**

## What it is not evidence for

- **Not a country risk ranking.** The denominator is organizations already hit; a country
  where few organizations are attacked but those that are get large demands will look
  "worse" here than one with the reverse. This says nothing about likelihood of attack.
- **Not a loss estimate.** A ransom demand is what an attacker asked for. A payment is what
  a victim transferred. Neither is the cost of the incident, and the recovery-cost column
  explicitly excludes ransoms.
- **Not a full distribution.** Each country cut publishes a median and one threshold
  (share of demands ≥ $1M). That is an exceedance statement, not a distribution — the
  sector cuts of the same survey carry banded charts, and the country cuts do not.
- **Not tail-inclusive.** Ransoms of $40M or more were removed before publication. Any
  reading of the upper tail from this data is reading a truncated one.

## How to check it

Every row is one verified audit entry with its artifact hash:

```bash
python -c "import yaml;print(yaml.safe_load(open('sources/audit.yaml'))['audit'])" | grep sophos_state_ransomware
python scripts/riskshard_doctor.py     # prints audit coverage
```

The underlying documents are the seven country cuts of *The State of Ransomware 2026*,
Sophos, July 2026, registered in [`sources/registry.yaml`](../sources/registry.yaml).
