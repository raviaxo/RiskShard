"""If a reader names a cell we never published, what would borrowing actually give them?

Roadmap U2 (the execution plan's W4) proposed turning the 456 unanswerable cells into
labelled answers by taking the nearest published shard's anchors and marking what was
borrowed. [ADR-0018](../docs/adr/0018-the-target-selector-failed-measurement.md)'s
amendment requires a differently-shaped design to state its own failure condition
**before** it ships, because ADR-0014 shipped a control decided on what the page could
cheaply compute and never on what its answers would say.

This module is that failure condition, made measurable. It builds no feature. It asks
the one question that decides whether the feature is worth building: **how many
distinct answers could a reader actually receive?**

**The ceiling is structural.** Under any borrowing rule the answer for a cell is some
published shard's answer, so the number of distinct answers can never exceed the number
of shards. 456 cells, 11 shards. No choice of donor rule changes that, and
[ADR-0016](../docs/adr/0016-the-audit-is-the-product.md) part 2 freezes the shard count,
so it cannot be raised by adding cells either.

**The tie rate is the sharper number.** "Nearest" is only meaningful if one shard is
nearer than the rest. For most empty cells several are equally near, and which figure
the reader receives then falls to a tiebreak carrying no evidentiary meaning at all —
sorting by id sends most of them to whichever shard sorts first.
"""
from collections import Counter
from itertools import product

from engine.cell_coverage import FACETS, _parameters, matched_count, offered_values

#: Facet weights from the intake scorer's own finding — sector is bridged far more
#: often than country, so a reader's sector is the costlier mismatch. Kept here to
#: test whether weighting rescues the design. It does not.
SECTOR_WEIGHTED = {"industry": 4, "threat": 3, "size": 2, "country": 1}


def _shard_cells(shards):
    facets = [facet for facet, _ in FACETS]
    return {s["id"]: {f: s.get(f) for f in facets if s.get(f)} for s in shards}


def empty_cells(shards):
    """Every nameable cell the corpus cannot answer — the population U2 would serve."""
    parameters = _parameters(shards)
    values = offered_values(shards)
    facets = [facet for facet, _ in FACETS]
    out = []
    for choice in product(*[[None] + values[facet] for facet in facets]):
        cell = {f: v for f, v in zip(facets, choice) if v}
        if cell and not matched_count(parameters, cell):
            out.append(cell)
    return out


def borrowing_profile(shards, weights=None):
    """What nearest-shard borrowing would produce, without building it.

    `distinct_answers` is the count that decides the design: a reader naming any of the
    empty cells receives one of this many figures. `tie_share` is how often the rule
    cannot pick a nearest shard at all and falls back on an arbitrary ordering.
    """
    weights = weights or {facet: 1 for facet, _ in FACETS}
    cells_of = _shard_cells(shards)
    donors, ties = Counter(), 0
    cells = empty_cells(shards)
    for cell in cells:
        scored = [(sum(weights[f] for f, v in cell.items() if cells_of[i].get(f) == v), i)
                  for i in cells_of]
        best = max(score for score, _ in scored)
        winners = sorted(i for score, i in scored if score == best)
        ties += len(winners) > 1
        donors[winners[0]] += 1
    return {
        "cells": len(cells),
        "shards": len(cells_of),
        "donors_used": len(donors),
        # Bounded by `shards` under any rule: a borrowed answer is a shard's answer.
        "distinct_answers": len(donors),
        "ties": ties,
        "tie_share": ties / len(cells) if cells else 0.0,
        "by_donor": dict(donors.most_common()),
    }
