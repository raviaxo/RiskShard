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

Two readings, and they answer different questions:

**Empty share** is how often the whole grid answers nothing. It is the headline.

**Trap pairs** are the specific cruelty: two facet values that each answer something
on their own and answer nothing together. A reader who picks one, sees evidence, then
adds the second and watches it go to zero has been walked into a dead end by the
control. `AU` answers 14 and `manufacturing` answers 4; `AU + manufacturing` answers
nothing.

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
