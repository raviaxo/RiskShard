# ADR-0028 — A geometric mean is its own measurement basis

- **Status:** Accepted (2026-11-20) — decided by the owner on the re-read finding
- **Date:** 2026-11-20
- **Deciders:** repo owner
- **Extends:** [`0007-construct-coherence.md`](0007-construct-coherence.md) (the vocabulary this
  adds a term to)
- **Related:** [`0026-a-re-read-is-a-declared-property.md`](0026-a-re-read-is-a-declared-property.md)
  (the campaign that found it), [`0027-a-floor-is-the-published-lower-bound.md`](0027-a-floor-is-the-published-lower-bound.md)
  (same session, same shape: a label that did not name the quantity)

## Context

Three records carry Cyentia IRIS 2022's *"typical financial cost ... $266K"* as `impact.min`, with
`measurement_basis: median_total_event_cost`.

**$266K is the geometric mean.** IRIS 2022's Table 3 publishes the row explicitly:

| minimum | 1st quartile | geometric mean | median | 3rd quartile | 95th | maximum | N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| $32 | $29K | **$266K** | **$259K** | $2M | $52M | $12B | 1,893 |

and the body text says *"the typical cost of a security incident is about $263K (as measured by the
median and geometric mean)"*. IRIS **2025** then confirms the convention changed, in its own
footnote: *"Prior IRIS used the geometric mean for a typical loss. Since the growing 'shoulder' in
lower part of the distribution pulls the geomean down, the median is better central measure for the
updated distribution."*

So the label named the wrong statistic, and the right one had no name in our vocabulary.

### Why the near-identical value does not make this cosmetic

$266K and $259K are 2.7% apart, so nothing much turns on the number. What turns on it is the
**label**, and [ADR-0007](0007-construct-coherence.md) exists because a label that does not name the
quantity is how incoherent ranges get composed without anyone noticing. The same report makes the
stakes obvious at the other end of the vocabulary: its **arithmetic mean is over $25M**, roughly a
hundred times the geomean, *"not a good measure of typical losses due to the long-tailed
distribution"*. A corpus that cannot distinguish geometric mean from arithmetic mean cannot warn
anyone about that gap.

## Decision

**Add `geometric_mean_total_event_cost` to the `measurement_basis` vocabulary**, and use it on the
three IRIS 2022 records. No value moves.

1. It joins `CENTRAL_TENDENCY_BASES` in [`engine/slot_roles.py`](../../engine/slot_roles.py). A
   geometric mean **is** a measure of central tendency, so the three records keep being flagged for
   occupying a `min` slot with a central-tendency anchor. Omitting it there would have quietly
   retired a published finding by renaming its subject.
2. The records record the published **median ($259K)**, **minimum ($32)**, **first quartile
   ($29K)** and **N (1,893)** alongside, so the figure we chose sits beside the ones we did not.

## Alternatives considered

- **Take the published median, $259K, and keep the existing label.** Cheaper, no vocabulary added,
  and rejected: it changes what we cite in order to fit our dictionary. It would also have moved a
  published figure — `cyentia_iris_2022_typical_cyber_event_loss_usd` is `impact.min` for the
  third-party-outage drift-watch scenario — which is a strange price to pay for avoiding one enum
  value.
- **Caveat only, change neither.** Rejected on [ADR-0027](0027-a-floor-is-the-published-lower-bound.md)'s
  reasoning, one week old and applied to itself: a label that names the wrong statistic is not an
  undisclosed limitation, it is wrong. Disclosure is the remedy for a figure that is right but
  narrow.
- **Fold it into `mean_total_event_cost`.** Rejected hardest. In this very report those two differ
  by about 100x.

## Consequences

- **One new vocabulary term**, and the vocabulary is now able to express a distinction a held
  report publishes. This is the 19th `measurement_basis` value.
- **No published value moves**, and the `slot_roles` finding is unchanged by construction.
- **Coherence reporting gets finer**: a range mixing a geometric mean with an arithmetic mean is now
  visible as such instead of reading as two medians.

## Open questions

1. **Do other records carry a geomean under a different label?** The campaign re-read 28 records;
   this vocabulary gap was found in one source. Unmeasured elsewhere, and worth a sweep when a
   reason to run one appears — not before, under [ADR-0016](0016-the-audit-is-the-product.md) part 1.
