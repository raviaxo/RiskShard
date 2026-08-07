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

---

## 1. The inputs, and what each one actually measures

| parameter | value | source | measures |
| --- | --- | --- | --- |
| `frequency.min` | 0.10 | Cyentia IRIS, global | `org_prevalence_loss_event` |
| `frequency.likely` | 0.54 | Sophos 2024, Australia reading (n=330) | `org_prevalence_incident` |
| `frequency.max` | 0.70 | Sophos 2023, Australia reading | `org_prevalence_incident` |
| `impact.min` | AUD 97,000 | Business Queensland, medium-business cybercrime cost | `mean_total_event_cost` |
| `impact.likely` | AUD 900,000 | Sophos AU 2025 mean recovery cost, **excluding ransom paid** | `cost_component` |
| `impact.max` | AUD 76,000,000 | Latitude Financial 1H23 ASX disclosure | `single_documented_event_loss` |

Both ranges are **mixed** — the anchors are not readings of the same quantity. Hold that
thought; it is section 4.

---

## 2. What the model says

Seeded run, 10,000 trials, BetaPert, seed 42:

- **Annualised loss** — AVG **AUD 6,590,045** · P95 **17,719,611** · P99 **25,010,450**

**These are not the numbers you size a limit against**, and this is the first trap. The
annualised figures fold frequency into severity: they answer *"what do I lose in a year?"*
An insurance limit applies **per occurrence**, so the right input is the severity distribution
— the `impact` range alone:

- **Per-event severity** — mean **AUD 13,281,133** · P95 **35,419,929** · P99 **47,071,942**

Anyone reading the shard's headline AVG of 6.6M and buying a 10M limit has quietly mixed up an
annual aggregate with a per-event severity.

## 3. The exceedance table — the actual decision input

Per single event, from the severity distribution above:

| limit (AUD) | P(event exceeds limit) | expected uncovered loss per event (AUD) |
| ---: | ---: | ---: |
| 1,000,000 | 95.15% | 12,302,924 |
| 2,500,000 | 86.48% | 10,941,669 |
| 5,000,000 | 73.68% | 8,942,573 |
| 10,000,000 | 51.90% | 5,822,157 |
| 15,000,000 | 34.79% | 3,680,367 |
| 20,000,000 | 22.93% | 2,250,635 |
| 25,000,000 | 15.06% | 1,314,513 |
| 30,000,000 | 9.48% | 715,532 |
| 50,000,000 | 0.56% | 24,065 |

**The naive answer:** a firm wanting ≤10% chance that a ransomware event exceeds its cover buys
**AUD 30M**. If it can live with roughly one-in-four, **AUD 20M**.

---

## 4. Why the naive answer is wrong, in dollars

The severity distribution's **mean is AUD 13.3M — 14.8× its own mode of AUD 900k**. That is not
a modelling quirk to wave through. It happens because a BetaPert is anchored on its maximum, and
this maximum is doing something it was never measured to do.

**The `max` is one company's disclosure, not a percentile.** AUD 76M is what Latitude Financial
reported for a single 2023 incident. It is a real, documented, verifiable loss — and it carries
**no exceedance probability whatsoever**. Nothing in the source says a mid-market firm has an
*x%* chance of a loss that size. Placed at the top of a PERT, it stops being a "worst case" and
starts driving the mean.

**The `likely` excludes ransom payments.** Sophos's AUD 900k is mean recovery cost *excluding
ransoms paid* — a `cost_component`, not a total. The central anchor is therefore systematically
low by whatever the ransom would have been.

So the two anchors are wrong in **opposite directions**: the mode understates because it is a
partial cost, and the maximum overstates the mean because it is a single tail observation with
no attached likelihood. The width between them is substantially a difference of *definition*,
not of *uncertainty* — and a limit decision reads that width as if it were uncertainty.

### Sensitivity: the max anchor alone decides the answer

Same floor, same mode, same seed. Only the maximum changes:

| max anchor (AUD) | mean | P95 | P(>20M) | P(>30M) | what it is |
| ---: | ---: | ---: | ---: | ---: | --- |
| **76,000,000** | 13,281,133 | 35,419,929 | **22.93%** | **9.48%** | Latitude disclosure (published) |
| 44,518,642 | 8,036,403 | 21,089,703 | 6.18% | 0.51% | Cyentia IRIS extreme, USD 32M @ RBA 0.7188 |
| 9,000,000 | 2,109,294 | 4,887,252 | 0.00% | 0.00% | illustrative only — 10× the mode, not a source |

The probability that a single event exceeds AUD 20M moves from **0% to 23%** depending on which
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
   loss starts flattening (2.25M at 20M against 1.31M at 25M — a 42% reduction in exposure for
   25% more limit; the next step buys much less).
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
