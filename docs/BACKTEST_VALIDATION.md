# Backtest Validation — Frequency vs. Open Incident Data

Most risk tools ask you to trust their numbers. This is a record of RiskShard
checking its own, in public, against open data — and reporting what held and what
did not.

Reproduce everything here with:

```bash
python scripts/backtest_frequency.py
```

Dataset: the **VERIS Community Database (VCDB)** — 10,000+ public security
incidents, CC BY-SA 4.0. We compared RiskShard's data-breach **frequency** model
for financial-services mid-market firms against the incident record.

## What held, and what didn't

**Scope: frequency only — and that itself is a finding.** VCDB carries a dollar
loss on only ~5% of incidents, so severity cannot be validated against it. That
is external confirmation of a caveat RiskShard already makes loudly: **frequency
is far more knowable than severity** (see [METHODOLOGY.md](METHODOLOGY.md)).

| Cell (finance data breach) | incidents, since 2015 | mean/yr | dispersion (var/mean) |
| --- | --- | --- | --- |
| United Kingdom (the shipped shard) | 21 | 4.2 | 1.6 |
| United States (data-rich check) | 284 | 25.8 | 28.0 |

Three honest results:

1. **The rate is plausible but not verifiable from VCDB.** VCDB captures only a
   small, non-random fraction of real incidents, so its counts are a floor, not a
   true rate — it cannot confirm an absolute frequency, only fail to contradict
   one. RiskShard's UK rate is in the same order of magnitude as national survey
   prevalence, so nothing here says it is wrong; but "plausible" is the honest
   word, not "proven."
2. **The frequency *shape* is wrong, and we can quantify it.** Real annual counts
   are heavily overdispersed (the data-rich US cell has variance ≈ 28× its mean).
   A negative-binomial fit puts the clustering parameter at **r ≈ 0.96 with a
   +122 log-likelihood gain over a Poisson** — meaning a smooth rate (what
   RiskShard uses today) understates how much incidents cluster year to year.
   This is a concrete model improvement now on the roadmap.
3. **Severity is not testable here.** With a dollar figure on ~5% of incidents,
   any severity "validation" would be manufactured. We don't do it.

## Honest caveats

- The UK sample is tiny (21 incidents), and VCDB's UK coverage thins after ~2019.
- The US overdispersion is partly a data artifact (VCDB is curated in waves and
  reflects breach-notification-law effects), so "frequency is fat-tailed" is
  directional, not a precise estimate.
- VCDB is US-dominated; other countries are too thin to test at all.

## Why publish this

An open, auditable risk library should be able to be wrong in public and show its
work. The backtest didn't produce a victory lap — it produced a to-do (a better
frequency model) and a boundary (severity we won't overclaim). That is the point.
