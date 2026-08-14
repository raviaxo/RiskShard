# ADR-0012 — The loss-event registry, as a bounded trial

- **Status:** Accepted (2026-08-13)
- **Date:** 2026-08-13
- **Deciders:** repo owner
- **Supersedes:** [`0005-documented-loss-event-registry.md`](0005-documented-loss-event-registry.md)
  (Deferred 2026-07-31).
- **Related:** [`0008-the-governed-tail.md`](0008-the-governed-tail.md) (the defect this would
  serve), [`0009-what-riskshard-is-and-is-not.md`](0009-what-riskshard-is-and-is-not.md) (the
  scope gate it must clear), [`0010-where-riskshard-stops.md`](0010-where-riskshard-stops.md)
  (the thesis that changed the calculus)
- **Measurement behind it:** [`../internal/edgar_corpus_census.md`](../internal/edgar_corpus_census.md)

## Context

ADR-0005 proposed a governed registry of publicly documented cyber loss events and was
**Deferred** for two stated reasons: no second maintainer, and *"it does not solve the mid-market
impact gap — it is a tail-and-defensibility instrument."*

Three things have changed.

**The thesis it was judged against was replaced.** [ADR-0010](0010-where-riskshard-stops.md) makes
the governed evidence object the product and the simulation a reference rendering. "It is only a
tail-and-defensibility instrument" is a demotion **only if** composing shard distributions is the
product. It no longer is.

**An independent practitioner named the same sources, unprompted.** Asked to sniff-test the
project, Adrian Sanabria — who maintains a breach dataset himself — answered that the three places
he finds loss numbers are **SEC filings, PACER documents, and cyber insurance claims-paid
reports**. That is ADR-0005's source triage, arrived at independently. He also declined to be the
second maintainer, so **that deferral condition is still unmet.**

**The corpus was measured rather than assumed.** ADR-0005 rested on a 20-filer sample. A full
census now exists.

## What the census found

| | |
| --- | --- |
| candidate issuers with a quantified incident figure | **50** |
| rejected on hand verification | **12** |
| surviving | **38** |
| carrying a directly usable event cost or impact | **~33** |
| candidates invisible to the ADR-0005 discovery method | **33 of 50** |

Three results matter more than the headline:

- **ADR-0005's *reach* was the defect, not its rate.** Its yield reproduced almost exactly (30% of
  filers with a later report, against ~27%). But starting from Item 1.05 finds a third of what is
  there: materiality is asserted at the incident, while the cost lands quarters later in a periodic
  report, sometimes with no 8-K ever filed. Matching periodic reports directly on cost phrases
  reaches the rest.
- **The corpus reaches genuinely small issuers.** Verified figures span roughly four orders of
  magnitude — about $25,000 to $345M, median ~$7.9M. ADR-0005 guessed the large-cap bias was "less
  absolute than assumed"; that is now measured, and it is the ADR's strongest surviving claim.
- **Nobody types the amounts.** Debevoise, Cherry Hill and Wilson Sonsini all track the *filings*
  with summaries; none extracts, types or attaches provenance to the *figures*. Commercial loss
  databases exist (Advisen holds ~150k events; Cyentia's IRIS is built on it) but are paywalled and
  distributed as derivatives, so no row is checkable by a reader. **The gap is openness and
  provenance, not discovery** — and any description of this work must say so rather than claim to
  have found the corpus.

**It is dozens, not hundreds.** The census does not support "this is a dataset play."

## What it would and would not fix

**It would not supply the missing denominator.** [ADR-0008](0008-the-governed-tail.md) leaves 7 of
11 maxima with `exceedance_basis: none_known`, and the honest reading is that ~33 heterogeneous
events across many sectors and countries give **no per-cell exceedance statistic**. Ranking a
maximum within a mixed bag of 33 would be a worse error than declaring nothing, and this ADR does
not propose it. The denominator remains unfound, here and anywhere else we have looked.

**It would not fix the mid-market gap**, and it cannot produce a central tendency. ADR-0005's three
structural biases stand unchanged: selection toward listed entities, materiality censoring at an
unknown threshold, and provisional figures that settle quarters later.

**What it would fix is smaller and real.** Five anchors already use a single documented event at
`impact.max` — `arup_2024_deepfake`, `afp_2020_au_bec`, `latitude_1h23`, `spf_2024_sg_bec`,
`coalition_2023_us_ftf` — each hand-researched, each recorded in a different shape, none reusable
by another shard or discoverable by a contributor, and **all five carrying `none_known`**. The
practice this ADR would govern *already exists, ungoverned*. Every future tail anchor repeats the
research.

It would also produce the artefact the defending moment actually needs: *"a company in this sector
disclosed this cost in an SEC filing"* is a matter of public record rather than a model output, and
it is checkable by the reader in thirty seconds.

## Scope gate

[ADR-0009](0009-what-riskshard-is-and-is-not.md) asks: *does this make an existing published number
more correct, or the method more sophisticated?*

It makes existing numbers more correct — governed, reusable, typed tail anchors in place of
one-off hand research — and introduces **no new measurement axis** and no new methodology. It
clears the gate. Note it does so **narrowly**: the claim is better anchors, not better statistics.

## Decision

**Adopted as a bounded trial, not as a curation commitment.**

The failure ADR-0005 correctly feared is an open-ended registry that goes stale and implies a
currency it does not have. The way to avoid it is not to defer forever but to bound the thing and
give it a kill criterion.

1. **One slice only.** The ~33 verified issuers already found, as governed loss-event records held
   to the same discipline as `evidence/` — named source, exact cited line, caveat, retrieval date,
   citable under [ADR-0004](0004-citable-parameter-identifiers.md).
2. **Every amount typed** — cost · impact · recovery · delta · settlement · fine. Five of the 38
   verified issuers carry something that is *not* a gross event cost, and mixing them produces
   nonsense.
3. **Verification-assisted, never automatic.** 12 of 50 machine candidates were wrong in six
   distinct ways. Units resolve against the statement header, not the sentence: AvidXchange's
   `$179` is $179,000, and SIFCO's `$3,000` is a coverage *limit*.
4. **No exceedance claims from it.** Entries are documented events. They may not be aggregated into
   an average, and they may not be ranked into an exceedance probability at this corpus size.
5. **Kill criterion, measured at two release cycles.** ADR-0005 already named the right metric:
   the count of shards whose `impact.max` cites a registry entry rather than a one-off, and whether
   anyone outside the project contributes an entry. **If neither has moved, retire the registry
   rather than carry it.** A retired experiment is a result; a stale registry is a liability.

Expansion beyond this slice — other jurisdictions, PACER, regulator penalty registers — is **not**
authorized here and needs its own decision once the maintenance path is proven.

## Alternatives considered

- **Defer again.** Defensible: the second-maintainer condition is genuinely still unmet, and the
  corpus is dozens. The argument against is that ADR-0005 deferred on a *thesis* that has since
  changed and on a *corpus size* that had not been measured. Both objections have now been
  answered, and deferring a second time on the same reasoning would be deferring on nothing new.
- **Adopt fully as the project's centre of gravity.** Rejected on the measurement. ~33 events is
  not a dataset, the biases are structural, and betting the project on it would be the overselling
  ADR-0005 explicitly warned against.
- **Take the commercial route** (license Advisen or similar). Rejected: it inverts the thesis. The
  scarce thing is a row a reader can check, and a paywalled derivative is precisely what cannot be
  checked.
- **Extract nothing; publish the census and stop.** The census is already published and already
  useful as a finding. This is the honest fallback if the trial is declined, and it costs nothing.

## Open questions for the owner

1. **Where do records live** — `loss_events/` alongside `evidence/`, or inside it? They are
   evidence about a company, not about a cell, and the distinction may deserve a directory.
2. **Do regulator fines and court settlements belong?** They are penalties and awards, not event
   losses, and ADR-0005 left this open. The census found both.
3. **Are non-cyber operational events in scope** (a grid failure, a payment-system outage)? Also
   left open by ADR-0005.
4. **Is the trial worth the labour at all**, given the second maintainer did not materialise? The
   owner accepted it on 2026-08-13 knowing that, which is what the kill criterion in decision 5 is
   for: the question is answered by the trial, not before it.
