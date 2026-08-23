# Worked decision — how much ransomware cover should an Australian mid-market financial firm buy?

A dataset that never produces a decision is a library of scary statistics. This is one
decision, made out loud, with the model, the seed, and the reasoning published so the argument
can be about the assumptions instead of the conclusion.

It is also the first place where the two governance axes
([ADR-0003](adr/0003-shared-impact-bridges.md) population match,
[ADR-0007](adr/0007-construct-coherence.md) measurement basis) change a number someone would
actually act on. That turns out to be the interesting part, so it is not confined to a footnote.

**Shard:** `au_finance_ransomware_midmarket` · **Reproduce:**
`python scripts/fair_calc.py scenarios/au_finance_ransomware_midmarket.yaml --seed 42`

> **Re-run 2026-08-23 on a refreshed anchor, and the recommendation is unchanged.**
> `impact.likely` moved from the Sophos Australia **2025** mean recovery cost (AUD 900,000) to the
> **2026** country cut (AUD 2,310,000) — same publisher, country and construct, successor edition.
> Every figure below is recomputed. **What survives:** the maximum still drives the mean, the
> anchors are still wrong in opposite directions, and **AUD 20M is still where the marginal
> exposure flattens — a 42% reduction from 20M to 25M, the same as before.**
> **What moved:** the mean-over-mode ratio fell from **14.8× to 6.16×**, because the mode nearly
> tripled while the maximum did not move. The argument that the mode is *understated* is
> correspondingly weaker in magnitude and unchanged in direction. P(event > 20M) rose 22.93% →
> **26.21%**. The 2025 figures are not restated here; the prior version is in git history.

---

## 1. The inputs, and what each one actually measures

| parameter | value | source | measures |
| --- | --- | --- | --- |
| `frequency.min` | 0.10 | Cyentia IRIS, global | `org_prevalence_loss_event` |
| `frequency.likely` | 0.54 | Sophos 2024, Australia reading (n=330) | `org_prevalence_incident` |
| `frequency.max` | 0.70 | Sophos 2023, Australia reading | `org_prevalence_incident` |
| `impact.min` | AUD 97,000 | Business Queensland, medium-business cybercrime cost | `mean_total_event_cost` |
| `impact.likely` | AUD 2,310,000 | Sophos AU **2026** mean recovery cost, **excluding ransom paid** | `cost_component` |
| `impact.max` | AUD 76,000,000 | Latitude Financial 1H23 ASX disclosure | `single_documented_event_loss` |

Both ranges are **mixed** — the anchors are not readings of the same quantity. Hold that
thought; it is section 4.

---

## 2. What the model says

Seeded run, 10,000 trials, BetaPert, seed 42:

- **Annualised loss** — AVG **AUD 7,079,188** · P95 **18,728,959** · P99 **25,872,131**

**These are not the numbers you size a limit against**, and this is the first trap. The
annualised figures fold frequency into severity: they answer *"what do I lose in a year?"*
An insurance limit applies **per occurrence**, so the right input is the severity distribution
— the `impact` range alone:

- **Per-event severity** — mean **AUD 14,229,567** · P95 **36,078,472** · P99 **47,370,001**

Anyone reading the shard's headline AVG of 7.1M and buying a 10M limit has quietly mixed up an
annual aggregate with a per-event severity.

## 3. The exceedance table — the actual decision input

Per single event, from the severity distribution above:

| limit (AUD) | P(event exceeds limit) | expected uncovered loss per event (AUD) |
| ---: | ---: | ---: |
| 1,000,000 | 96.18% | 13,245,365 |
| 2,500,000 | 88.94% | 11,858,129 |
| 5,000,000 | 76.80% | 9,790,654 |
| 10,000,000 | 55.68% | 6,495,224 |
| 15,000,000 | 39.40% | 4,142,646 |
| 20,000,000 | 26.21% | 2,514,059 |
| 25,000,000 | 16.68% | 1,459,694 |
| 30,000,000 | 10.09% | 799,107 |
| 50,000,000 | 0.66% | 28,102 |

**The naive answer:** a firm wanting ≤10% chance that a ransomware event exceeds its cover buys
**AUD 30M**. If it can live with roughly one-in-four, **AUD 20M**.

---

## 4. Why the naive answer is wrong, in dollars

The severity distribution's **mean is AUD 14.2M — 6.16× its own mode of AUD 2.31M**. That is not
a modelling quirk to wave through. *(It was 14.8× against a mode of AUD 900k until the 2026 anchor
landed on 2026-08-23. The ratio nearly halved because the mode tripled and the maximum did not move
at all — which is itself the point of this section.)* It happens because a BetaPert is anchored on its maximum, and
this maximum is doing something it was never measured to do.

**The `max` is one company's disclosure, not a percentile.** AUD 76M is what Latitude Financial
reported for a single 2023 incident. It is a real, documented, verifiable loss — and it carries
**no exceedance probability whatsoever**. Nothing in the source says a mid-market firm has an
*x%* chance of a loss that size. Placed at the top of a PERT, it stops being a "worst case" and
starts driving the mean.

**The `likely` excludes ransom payments.** Sophos's AUD 2.31M is mean recovery cost *excluding
ransoms paid* — a `cost_component`, not a total. The central anchor is therefore systematically
low by whatever the ransom would have been, and in the 2026 edition that gap widened in both
directions at once: **57%** of Australian organisations paid and got data back (up from 41%), at a
**median payment of USD 855,000** (up from USD 350,000). The understatement is larger in dollars
and smaller as a fraction of a mode that tripled.

So the two anchors are wrong in **opposite directions**: the mode understates because it is a
partial cost, and the maximum overstates the mean because it is a single tail observation with
no attached likelihood. The width between them is substantially a difference of *definition*,
not of *uncertainty* — and a limit decision reads that width as if it were uncertainty.

### Sensitivity: the max anchor alone decides the answer

Same floor, same mode, same seed. Only the maximum changes:

| max anchor (AUD) | mean | P95 | P(>20M) | P(>30M) | what it is |
| ---: | ---: | ---: | ---: | ---: | --- |
| **76,000,000** | 14,229,567 | 36,078,472 | **26.21%** | **10.09%** | Latitude disclosure (published) |
| 44,518,642 | 8,942,190 | 21,922,843 | 7.42% | 0.64% | Cyentia IRIS extreme, USD 32M @ RBA 0.7188 |
| 9,000,000 | 3,076,317 | 5,977,607 | 0.00% | 0.00% | illustrative only — 10× the mode, not a source |

The probability that a single event exceeds AUD 20M moves from **0% to 26%** depending on which
maximum you pick. The frequency evidence, the floor, and the mode are untouched. **The limit
decision is a decision about one anchor**, and that anchor is currently a single company's bad
year.

---

## 5. The decision

**Buy AUD 20M, and treat the number as a floor under review rather than an answer.** Reasoning:

1. **Do not buy to the 76M anchor.** It is one observation. Sizing cover to it means buying
   against a tail whose probability nobody has estimated, and paying premium for it every year.
2. **Do not buy below ~15M either.** The floor and mode are both *understated* — the mode
   excludes ransom outright — so the left side of this distribution is soft in the direction of
   too little cover, not too much.
3. **20M sits where the two errors partly offset** and where the marginal expected uncovered
   loss starts flattening (2.51M at 20M against 1.46M at 25M — **a 42% reduction** in exposure for
   25% more limit; the next step buys much less). *That 42% is unchanged by the 2026 refresh: both
   figures rose by roughly the same proportion, so the shape of the curve — which is what the
   decision reads — survived a 2.55× move in the mode.*
4. **Latitude is the reason to hold the position, not to abandon it.** A documented Australian
   financial-services extortion loss at 76M is exactly the event a limit exists for. It belongs
   in the record. It just does not belong as a PERT maximum without a stated exceedance
   probability.

**What would change this decision:** a published severity *distribution* for Australian
mid-market ransomware — even three points with probabilities attached — would replace the
single-observation maximum and could move the recommendation by 10M in either direction. A
ransom-inclusive recovery cost would raise the mode and the floor. Neither exists publicly today
(scouted 2026-08-02/03; recorded in the internal queue).

---

## 6. What this is not

- Not advice. It is one modelled argument with its inputs exposed, for a synthetic mid-market
  Australian financial-services firm.
- Not benchmark-grade. This shard is `governed_starter`; no item in this repository has passed a
  recorded human review.
- Not a claim that the range is sound. It is **mixed on both axes** and the whole point of
  section 4 is what that costs.

**Break it.** If the sensitivity reasoning is wrong, or 20M is the wrong read of that table,
say so — [open an issue](https://github.com/raviaxo/RiskShard/issues/new) or reply on the
"[Break a number](https://github.com/raviaxo/RiskShard/discussions/106)" discussion. A confirmed
break is retracted publicly and credited by handle.

## 7. Reproduce it

```bash
python scripts/fair_calc.py scenarios/au_finance_ransomware_midmarket.yaml --seed 42
python scripts/riskshard_modules.py provenance au_finance_ransomware_midmarket
python scripts/riskshard_modules.py coherence au_finance_ransomware_midmarket
python scripts/riskshard_modules.py export au_finance_ransomware_midmarket --format pyfair
```

Severity and exceedance figures come from the `impact` range under the same derived seed; FX uses
the governed RBA F11.1 assumption (A$1 = USD 0.7188) in `calibrations/fx_rates.yaml`.
