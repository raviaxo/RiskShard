"""Cell coverage: how many targets a reader could name that this corpus can answer.

ADR-0018 retired the reader-supplied target selector on a measurement rather than an
argument: the control offered a reader a grid of facet combinations, and its most
common answer was that the corpus held nothing for them.

That ADR then set preconditions for ever building it again, and a precondition
written as prose goes stale the moment the corpus moves. Worse, the first
measurement behind it was taken by an ad-hoc script that read the size facet under
the wrong key (`sizes` rather than `company_size_bands`), so size was never tested
and the grid was undercounted 539 -> 215. The finding survived the correction and
got stronger; the numbers did not. That is precisely why this lives in the engine
with a test on it instead of in a document.

Four readings, and they answer different questions:

**Empty share** is how often the whole grid answers nothing. It is the headline.

**Trap pairs** are the specific cruelty: two facet values that each answer something
on their own and answer nothing together. A reader who picks one, sees evidence, then
adds the second and watches it go to zero has been walked into a dead end by the
control. `AU` answers 14 and `manufacturing` answers 4; `AU + manufacturing` answers
nothing.

**Specificity profile** splits the grid by how much the reader said. The empty share
averages over readers who named one facet and readers who named four, and those are
not the same question. Split apart, the corpus answers the first every time and the
last almost never: supplying context makes the answer worse.

**Shard self-coverage** turns the same rule on ourselves, per shard. The corpus total
is already published (`params_cell_matched`, 7 of 66); how those 7 distribute is not,
and they are not spread thinly across eleven shards but concentrated in four. Seven
shards match none of their own parameters and none is complete on its own cell. That
is a disclosure owed on numbers already published, not a finding about a feature we
might build.

The rule replicated here is the engine's own: a parameter is bridged on a facet when
the population it declares does not name the target's value for that facet, and a
facet the target leaves unset is not tested. Wildcard declarations (`all`, `global`,
`any`) are never offered as choices, because offering a value nothing was measured on
invites a question this corpus cannot answer.
"""
from itertools import combinations as _pairs, product

FACETS = (("country", "countries"), ("industry", "industries"),
          ("size", "company_size_bands"), ("threat", "threats"))
WILDCARDS = frozenset({"all", "global", "any"})


def _parameters(shards):
    return [p for s in shards for p in (s.get("params") or [])]


def offered_values(shards):
    """Every facet value the selector would offer: declared populations plus our own cells."""
    values = {facet: set() for facet, _ in FACETS}
    for shard in shards:
        for facet, _ in FACETS:
            if shard.get(facet):
                values[facet].add(shard[facet])
        for param in shard.get("params") or []:
            declared = param.get("declared_for") or {}
            for facet, plural in FACETS:
                for value in declared.get(plural) or []:
                    if value not in WILDCARDS:
                        values[facet].add(value)
    return {facet: sorted(vals) for facet, vals in values.items()}


def matched_count(parameters, cell):
    """Parameters whose declared population names every facet the target sets."""
    total = 0
    for param in parameters:
        declared = param.get("declared_for") or {}
        for facet, plural in FACETS:
            want = cell.get(facet)
            names = declared.get(plural) or []
            if want and names and want not in names:
                break
        else:
            total += 1
    return total


def cell_coverage(shards):
    """Replay every target a reader could name and report what the corpus answers."""
    parameters = _parameters(shards)
    values = offered_values(shards)
    facets = [facet for facet, _ in FACETS]

    singles = {
        (facet, value): matched_count(parameters, {facet: value})
        for facet in facets
        for value in values[facet]
    }

    answered_by_value = {key: 0 for key in singles}
    total = empty = 0
    for choice in product(*[[None] + values[facet] for facet in facets]):
        cell = {facet: value for facet, value in zip(facets, choice) if value}
        if not cell:
            continue
        total += 1
        if matched_count(parameters, cell):
            for item in cell.items():
                answered_by_value[item] += 1
        else:
            empty += 1

    # Values that answer nothing anywhere: offering them is offering a trap.
    dead_ends = sorted(f"{f}={v}" for (f, v), n in answered_by_value.items() if n == 0)

    # Pairs that each answer alone and answer nothing together. This is the shape a
    # reader actually walks into, one dropdown at a time.
    traps = []
    for (fa, va), (fb, vb) in _pairs(sorted(singles), 2):
        if fa == fb or not singles[(fa, va)] or not singles[(fb, vb)]:
            continue
        if not matched_count(parameters, {fa: va, fb: vb}):
            traps.append(f"{fa}={va} + {fb}={vb}")

    answered = total - empty
    return {
        "parameters": len(parameters),
        "combinations": total,
        "answered": answered,
        "empty": empty,
        "empty_share": (empty / total) if total else 0.0,
        "dead_ends": dead_ends,
        "trap_pairs": sorted(traps),
        # ADR-0018's preconditions for reconsidering the retired control.
        "no_traps": not dead_ends and not traps,
        "majority_answered": total > 0 and answered * 2 > total,
    }


def specificity_profile(shards):
    """Does answering a reader get better or worse as they say more about themselves?

    The empty share is a single number over a grid that mixes a reader who named
    only a country with one who named country, industry, size and threat. Those are
    not the same question, and averaging them hides the finding.

    Split by how many facets the reader set and the corpus answers a reader who says
    nothing about themselves every time, and a reader who describes themselves
    precisely almost never. **Supplying context makes the answer worse**, which is
    the exact inverse of what a target selector promises. That is a different defect
    from a thin corpus: reading more sources raises the totals, but it does not by
    itself reverse the direction.

    `best_matched` is the ceiling at each level: the most parameters any single cell
    of that specificity matches. A shard needs all six to run, so a level whose
    ceiling is below six cannot produce a complete answer from matched anchors alone
    however many cells it answers.
    """
    parameters = _parameters(shards)
    values = offered_values(shards)
    facets = [facet for facet, _ in FACETS]

    levels = {}
    for choice in product(*[[None] + values[facet] for facet in facets]):
        cell = {facet: value for facet, value in zip(facets, choice) if value}
        if not cell:
            continue
        level = levels.setdefault(len(cell), {"cells": 0, "answered": 0, "best_matched": 0})
        matched = matched_count(parameters, cell)
        level["cells"] += 1
        level["answered"] += 1 if matched else 0
        level["best_matched"] = max(level["best_matched"], matched)

    for level in levels.values():
        level["empty"] = level["cells"] - level["answered"]
        level["answered_share"] = level["answered"] / level["cells"] if level["cells"] else 0.0

    shares = [levels[n]["answered_share"] for n in sorted(levels)]
    return {
        "levels": levels,
        # True when every extra facet a reader sets lowers their chance of an answer.
        "inverted": all(a > b for a, b in zip(shares, shares[1:])),
    }


def shard_self_coverage(shards):
    """Can a shard answer the cell it is named after?

    `engine/provenance.py` already answers this for the corpus: `params_cell_matched`
    is 7 of 66, and ADR-0013 corrected it from a hand-kept 31. What it does not answer
    is where those 7 sit. This does, and they are not spread thinly across eleven
    shards — four shards hold all of them and seven hold none.

    That distribution is the disclosure the explorer already tries to make and never
    has. `scripts/explorer_template.html` renders a per-shard split from
    `t.params_cell_matched`, guarded by a null check; `provenance.py` sets that field
    only on `totals`. So the guard is false on every shard on every build and the
    split silently renders as an empty string. A disclosure that degrades to nothing
    is worse than one that was never attempted, because the page reads as complete.

    A parameter counts as measured on the shard's own cell only when its declared
    population names every facet that cell sets, under the same rule the rest of this
    module uses. A wildcard (`all`, `global`) is not a name: a figure declared for
    every country was not measured on Australia, it was measured across a population
    that includes it. That is ADR-0003's definition of bridged, reproduced here
    rather than imported so this measurement cannot silently inherit a redefinition.

    Reported per shard because the answer varies from half to none, and the corpus
    average conceals exactly the shards that are worst off.
    """
    rows = []
    for shard in shards:
        cell = {facet: shard[facet] for facet, _ in FACETS if shard.get(facet)}
        own = list(shard.get("params") or [])
        matched = matched_count(own, cell) if cell else 0
        rows.append({
            "id": shard.get("id"),
            "cell": cell,
            "facets_set": len(cell),
            "parameters": len(own),
            "matched": matched,
            "bridged": len(own) - matched,
            "bridged_share": (len(own) - matched) / len(own) if own else 0.0,
        })

    rows.sort(key=lambda row: (row["matched"], row["id"] or ""))
    answering = [row for row in rows if row["matched"]]
    return {
        "shards": rows,
        "answering_own_cell": len(answering),
        "fully_bridged": sum(1 for row in rows if not row["matched"]),
        "best_matched": max((row["matched"] for row in rows), default=0),
        # No shard reaching six cannot be read as "some shards are fine": it means
        # every published figure rests partly on a population that is not its own.
        "any_shard_complete_on_own_cell": any(
            row["matched"] == row["parameters"] and row["parameters"] for row in rows),
    }


def answered_split(shards):
    """Of the cells that answer something, how many are cells we actually publish?

    "83 of 539 answer" invites the reading that the corpus is thin but pointed at our
    own eleven cells. It is not pointed there at all. Seven of the eleven shard cells
    answer nothing, so only four appear in the 83, and the other 79 are combinations
    we have never published a figure for — `financial_services + mid_market +
    data_breach` with no country named answers five parameters and is not a shard.

    This matters for scope rather than for coverage: ADR-0016's 2026-08-22 amendment
    draws the correctness boundary at the published cell, and the 83 is not a proxy
    for it. Being answerable is not the same as being published.
    """
    parameters = _parameters(shards)
    values = offered_values(shards)
    facets = [facet for facet, _ in FACETS]
    published = {
        tuple(sorted((facet, shard[facet]) for facet, _ in FACETS if shard.get(facet)))
        for shard in shards
    }

    answered = shard_cells = 0
    for choice in product(*[[None] + values[facet] for facet in facets]):
        cell = {facet: value for facet, value in zip(facets, choice) if value}
        if not cell or not matched_count(parameters, cell):
            continue
        answered += 1
        if tuple(sorted(cell.items())) in published:
            shard_cells += 1

    return {
        "answered": answered,
        "published_cells": shard_cells,
        "unpublished_cells": answered - shard_cells,
        "shards": len(published),
    }
