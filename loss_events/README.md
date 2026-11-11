# Loss events

Publicly documented cyber loss events with quantified financial impact. Governed by
[`../schemas/loss_event_schema.json`](../schemas/loss_event_schema.json) and decided by
[ADR-0012](../docs/adr/0012-loss-event-registry-bounded-trial.md), which supersedes ADR-0005.

> ## ⚠️ This trial is retired
>
> **The ADR-0012 bounded trial was retired on 2026-11-11, on its own pre-committed criterion.**
> [ADR-0017](../docs/adr/0017-the-kill-criterion-gets-a-clock.md) fixed the measurement at the
> first release on or after 2026-11-01; it was taken on 2026-11-11 and **both metrics read zero** —
> 0 of 11 shards cite an entry (0 *could*), 0 entries contributed from outside.
> [ADR-0025](../docs/adr/0025-the-registry-trial-is-retired.md) records the outcome.
>
> **The 36 events are kept as a published dataset with no claim on the shards.** Nothing is
> deleted and citations may pin it. What it lost is standing: **no shard parameter may cite a
> registry entry, and this registry makes no claim to calibrate anything.** The typing of the 48
> amounts — 12 of which are not event costs — remains its most useful property, and the three
> things it cannot do, below, are why.
>
> Both zeros are true and **neither is about adoption**: the registry was built on a corpus that
> structurally cannot serve the grid it was meant to serve, and was forbidden from growing into a
> shape that could.

**A record here describes one organisation's one incident.** That is what makes it different in
kind from everything in [`../evidence/`](../evidence/), where a record describes a *cell* — a
country × sector × size × threat population. Different question, different schema, different
directory.

## Read this before using a figure

**Every amount is typed, and the type is the point.** The corpus mixes gross event costs with
insurance recoveries, court settlements, revenue impacts and period-over-period deltas. Summing or
averaging across those types produces a number that means nothing. Of the amounts currently held,
**a quarter are not event costs at all** — they are money received, money awarded, or a change
between two periods.

Use `gross_event_amounts()` in [`../engine/loss_events.py`](../engine/loss_events.py) unless you
specifically want the others, and say so at the call site if you do.

**Three things this registry cannot do**, none of which curation can fix:

1. **No central tendency.** The corpus is selection-biased toward listed entities and censored at
   each filer's own materiality threshold. An average computed from it would describe nothing.
2. **No exceedance probability.** Three dozen heterogeneous events across many sectors and
   countries give no per-cell exceedance statistic. Ranking a maximum inside them would be a worse
   error than declaring `none_known`.
3. **No mid-market representation.** These are companies with disclosure obligations. The corpus
   does reach small issuers — the smallest figure held is about $25,000 — but it is not a sample of
   the mid-market cells the shards model.

What it *is* good for: **the tail, and defensibility.** *"A company in this sector disclosed this
cost in a filing"* is a matter of public record rather than a model output, and a reader can
confirm it in thirty seconds by opening the URL on the record.

## Accuracy obligations

These records name identifiable companies and their losses. Everything is drawn from public
filings, so it is factual and publishable, but it must stay strictly neutral and quote-accurate:

- `cited_line` is the filing's own sentence, quoted and not paraphrased.
- `event.description` is factual — no characterisation, no blame, no inference beyond the filing.
- `limitations` is never empty.
- `date_precision` is declared, never inferred. A month recorded as an exact day is unrecoverable
  once stored, which is a defect we measured in someone else's dataset and will not reproduce here.

## Two hazards that produced real errors

**Units.** Statement tables are denominated in thousands. A face-value read is wrong by 1000×.
AvidXchange's `$302` is $302 thousand; SIFCO's `$3,000` is a $3M coverage *limit* and not a loss at
all. Any amount below 10,000 must declare `units_resolved_from`, and a test enforces it.

**Bundling.** Halliburton disclosed a `$116M` pre-tax charge *"primarily related to severance
costs, an impairment of assets held for sale, expenses related to a cybersecurity incident."* One
number, three unrelated things. An extractor that takes the figure nearest the incident language
inherits the whole charge. Such filings are excluded rather than apportioned.

## How records are made

**Verification-assisted, never automatic** — ADR-0012 requires it, because 12 of 50 machine
candidates in the [census](../docs/internal/edgar_corpus_census.md) were wrong in six distinct ways.

Candidates come from [`edgar_corpus_census.py`](../docs/internal/research/edgar_corpus_census.py).
Records are emitted from the hand-verified table in
[`loss_event_extraction.py`](../docs/internal/research/loss_event_extraction.py) — that table *is*
the verification. **Do not hand-edit the YAML**: change the table and regenerate, so a record and
its verification cannot drift apart.

```bash
python docs/internal/research/loss_event_extraction.py > loss_events/sec_filings_2023_2026.yaml
python scripts/riskshard_doctor.py        # the registry has its own gate
```

## This was a bounded trial, and it ended

ADR-0012 adopted the registry **with a retirement test**, measured at two release cycles:

- how many shards anchor `impact.max` on a registry entry rather than a one-off, and
- whether anyone outside the project contributes an entry.

**If neither has moved, the registry is retired rather than carried.** A stale registry is worse
than none, because it implies a currency it does not have. `trial_metrics()` computes both numbers
and the doctor prints them every run, so the criterion is visible rather than remembered.

### Every reading, first to last: 0 shards cite an entry, and **0 could**

That second number is the one that matters, and it is why `citation_candidates()` exists. *"Nobody
cited an entry"* argues for retirement only if somebody **could** have. Measured across all 11
shards:

- **10 of 11 have no country-and-threat match at all.** The corpus is US/GB/IE; the shards are
  AU · CA · DE · FR · GB · JP · SG · US. And the registry holds **no business-email-compromise
  events**, so the three BEC shards cannot match on any corpus of this shape.
- **1 shard has genuine matches and is still blocked.** `us_finance_data_breach_midmarket` matches
  four events on country and threat, two of them on industry as well. But its current `impact.max`
  carries `observed_rank` — one of only two informative exceedance statements in the portfolio —
  and a registry entry carries none by rule. **Swapping would trade an exceedance statement for
  provenance**, which is a regression under [ADR-0008](../docs/adr/0008-the-governed-tail.md).

**This section said "the trial is still running, not failing" from 2026-08-14 until the
measurement.** That was true every time it was read and it is now the record of a trial that ran
its course. Zero citations here means *nothing fits yet*, not *nobody bothered* — and that
distinction **argued for retirement rather than against it**, because a registry that cannot serve
the shards is not waiting on readers.

What would have changed it: a non-US slice, BEC events, or a shard whose maximum declares
`none_known` and finds a country-and-threat match. None arrived, and under
[ADR-0016](../docs/adr/0016-the-audit-is-the-product.md) the registry was never permitted to grow
into the shape that would have supplied them.

Expansion beyond this slice — other jurisdictions, PACER, regulator penalty registers — was never
authorized and is now moot. Reopening any of it takes a new ADR and a measured defect, not a
change of mind.
