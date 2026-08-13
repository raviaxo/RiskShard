# Destroyed by Breach — what the dataset actually contains

*Internal working doc (governed by [`../../AGENTS.md`](../../AGENTS.md)). Measurement, not a
proposal. Pairs with [`destroyed_by_breach_scout.md`](destroyed_by_breach_scout.md), which is the
pre-contact scout and whose central premise this file corrects.*

- **Measured:** 2026-08-12 · **Delivered to the maintainer:** 2026-08-13
- **Source:** Adrian Sanabria, [destroyedbybreach.com](https://destroyedbybreach.com), shared by
  him as a public Google Sheet export on first contact
- **Entries:** 37 (the scout and his own description both said 35)

## Method

The published Sheet was exported to CSV and every entry run through the loss-record fields we
offered him — entity, date, figure, currency, what the figure measures, gross or net of recovery,
primary source per figure. Nothing was inferred, converted or estimated; every classification is
read off the text of the entry it sits on.

Columns present: `Organisation · Industry · Size (emp) · Location · Action · Actor · Motive ·
Outcome · What killed the company? · Earliest Date of Breach · Business Close Date · References`.

**There is no figure column.**

## Finding 1 — 0 of 37 entries carry the cost of the breach to the company

Four entries contain a currency amount, all inside the free-text `Outcome` field. All four measure
a different quantity, and none is the loss:

| Entry | Amount | What it actually measures |
| --- | --- | --- |
| Impairment Resources, LLC | USD 583,000 | loan balance owed to a creditor at Chapter 7 liquidation |
| Impairment Resources, LLC | < USD 250,000 | total asset value at liquidation |
| Best Medical Transcription | USD 200,000 | court settlement — one legal component; the fatal loss (lost primary client) is unquantified |
| Brookside ENT and Hearing Center | USD 6,500 | ransom **demanded and explicitly refused** — never paid |
| Creditag | BRL 15,000 | bribe paid **by the attackers** to an employee for credentials |
| Creditag | "tens of millions" | funds funnelled through the wider C&M Software scheme, not Creditag's own loss |

Because the amounts live in prose rather than a field, any mechanical read of this dataset collects
these as though they were comparable. Two are not the victim's money at all; one is a payment that
never happened.

## Finding 2 — the day of the month is not real in roughly half the rows

Breach dates are stored to the day, in a uniform `Month D, YYYY` format across all 37 entries.
**15 fall on the 1st**; 18 fall on the 1st, 30th or 31st, against roughly 4 expected if the days
were genuine. Those rows are a month or a year rendered as an exact date, and once stored the
distinction is unrecoverable.

This is the observation the queue had been holding back as a sequenced second message. It is now
measured rather than suspected, and it went out as part of the extraction rather than as a
standalone note.

## Finding 3 — 12 of 37 entries cite no source

Including Mt. Gox, AMCA, Code Spaces and Cryptopia. Twenty entries carry exactly one reference;
five carry two or more.

## What this means for ADR-0005 and ADR-0008 commitment 3

**The premise both rest on is withdrawn as stated.** The scout reasoned that a documented
loss-event registry is an exceedance denominator, that our seven undeclared maxima need exactly
that, and that this registry is one. The first two hold. The third does not.

**This is a mortality register, not a loss registry.** It answers *which organisations died
following a breach* — a numerator for P(death | breach), still lacking its own denominator — and
not *how often a loss of size X is exceeded*. Those are different statistics, and treating one as
the other is the error class this project exists to catch. It is recorded here because we asserted
the conflation to him in writing before measuring it.

What survives is real: the register is rare, openly maintained, and he handed over the whole thing
on first contact. A loss-carrying registry would still be the denominator we lack — it does not yet
exist, here or anywhere we have looked, and adding figures to this one is the offer already on the
table.

## Admissibility

**Not a source.** Nothing here enters `sources/manifest.json`: there are no loss figures to cite,
and a third of the entries carry no reference to verify against. If figures are ever added, each
would be assessed on its own primary source, never on the register's aggregate.

## Delivered

The full 37-entry extraction was sent to the maintainer as a published exhibit and a CSV, with all
three findings and their counts, ending on what the dataset *is* rather than what it lacks. No
figure was inferred on his behalf.
