"""If the READER picks the donor, is the choice real or is it laundered arbitrariness?

[ADR-0019](../docs/adr/0019-borrowing-cannot-answer-an-unpublished-cell.md) declined
rule-chosen nearest-shard borrowing on a measurement: 456 unanswerable cells would have
become 456 relabelled copies of 11 numbers, and **59.4% of those cells have no single
nearest shard**, so which figure a reader received fell to a tiebreak carrying no
evidentiary meaning. That ADR named three things that would change the defect. Two are
closed — more shards by ADR-0016 part 2, and per-cell evidence as the far heavier
ADR-0006 depth axis. The live one is **"the reader picks the donor"**, and ADR-0019 says
of it: *"That is a different feature with a different failure mode, and it would need its
own measurement."*

This module is that measurement. **It builds no feature.**

## The failure condition, fixed before anything was computed

[ADR-0018](../docs/adr/0018-the-target-selector-failed-measurement.md)'s amendment makes
this mandatory, and pre-states the shape for composition — *a feature whose most common
output is "this figure is entirely borrowed" may teach readers to distrust*. For
reader-chosen donors that is **not** the sharp risk, because such a design discloses the
borrowing by construction; the reader is the one doing it.

The sharp risk is different and worse:

> **If the tied donors are indistinguishable, the feature converts a rule's arbitrary
> tiebreak into the reader's arbitrary tiebreak and calls the difference agency.**

ADR-0019 killed the rule version because a meaningless tiebreak decided the answer.
Handing that same tiebreak to the reader does not make it meaningful. It makes it
*theirs*, and dressing an arbitrary pick as an informed choice is a worse failure than
declining to answer, because the reader now believes they exercised judgement.

So a reader-chosen donor is worth building only if, when donors tie, the reader has
something real to choose **on**. Two things could give them that:

1. **Different matched facets.** Two donors tied at "2 of 4 facets" are distinguishable
   if one matches country+threat and the other industry+size — a reader who knows their
   threat matters more than their sector can act on that. If every tied donor matches the
   *same* facet set, there is nothing to act on.
2. **Materially different values.** If the tied donors' figures are nearly identical the
   choice does not change the answer, so it does not matter which is picked — harmless,
   but also not a feature worth building.

### The thresholds, fixed now, before the first run

**Decline if EITHER holds:**

- **more than 50%** of tied cells offer only **one** distinct matched-facet set among
  their tied donors — the reader has no stated basis to choose; or
- **more than 50%** of tied cells have a value spread across tied donors of **under
  25%** (max/min on the composed impact figure) — the choice does not move the answer
  enough to be worth asking for.

Both numbers are written here before `measure()` was ever run, for the reason ADR-0017
exists as a standing warning: a threshold chosen after seeing the distribution is not a
test. Either condition firing declines the feature; the remaining route to the defect is
then per-cell evidence, which is the depth axis and a different programme.

**What a pass would mean.** Not that the feature is good — only that the reader is being
offered a real choice rather than a coin flip with a label on it. The design would still
owe its own disclosure and its own second measurement before it reached a page.
"""

import re

from engine.borrowing import FACETS
from engine.currency import (CurrencyConversionError, convert_currency,
                             load_fx_rates)


def _shard_facets(shard):
    """The facet values a shard publishes, as sets, for membership testing."""
    out = {}
    for facet, plural in FACETS:
        value = shard.get(facet) or shard.get(plural)
        if value is None:
            out[facet] = frozenset()
        elif isinstance(value, (list, tuple, set, frozenset)):
            out[facet] = frozenset(value)
        else:
            out[facet] = frozenset([value])
    return out


def _matched_set(shard_facets, cell):
    """WHICH facets a donor matches for this cell, not how many.

    The distinction is the whole measurement: a count ties, a set may not.
    """
    return frozenset(
        facet for facet, _ in FACETS
        if cell.get(facet) is not None and cell[facet] in shard_facets[facet]
    )


_AVG = re.compile(r"^\s*([A-Z]{3})\s*([\d,]+(?:\.\d+)?)\s*$")


def _impact(shard, fx_rates=None):
    """One comparable figure per donor, in a single currency, for the spread test.

    The explorer publishes `avg` as a formatted string carrying its own currency —
    "AUD 154,814.52". The eleven shards do not share one, so comparing the raw numbers
    would compare a currency difference and call it a disagreement about loss. Every
    figure is converted to USD through the governed FX table before any spread is taken.

    Returns None when the figure cannot be parsed or converted. A cell whose donors have
    no comparable figure is **excluded** from the spread test, never counted as agreeing
    — the first draft of this module let an unparsed figure fall through to zero
    comparable cells and still report `declines_on_values: false`, which is a test that
    did not run reporting as a test that passed.
    """
    raw = shard.get("avg")
    if not isinstance(raw, str):
        return None
    match = _AVG.match(raw)
    if not match:
        return None
    currency, amount = match.group(1), float(match.group(2).replace(",", ""))
    if currency == "USD":
        return amount
    if fx_rates is None:
        return None
    try:
        # convert_currency returns a provenance record, not a bare number.
        return float(convert_currency(amount, currency, "USD", fx_rates)["value"])
    except CurrencyConversionError:
        return None


def measure(shards, cells, fx_rates=None):
    """Run the condition above over every tied cell. Computes nothing it does not report.

    `cells` is the empty-cell list from `engine.borrowing.empty_cells`.
    """
    if fx_rates is None:
        fx_rates = load_fx_rates()
    facets_by_shard = {s["id"]: _shard_facets(s) for s in shards}
    impact_by_shard = {s["id"]: _impact(s, fx_rates) for s in shards}
    if not any(impact_by_shard.values()):
        raise ValueError(
            "no donor figure could be parsed, so the value-spread half of the condition "
            "cannot run — refusing to return a verdict that rests on an unmeasured test"
        )

    tied_cells = 0
    single_facet_set = 0
    comparable = 0
    narrow_spread = 0
    spreads = []

    for cell in cells:
        scored = []
        for shard in shards:
            matched = _matched_set(facets_by_shard[shard["id"]], cell)
            scored.append((len(matched), matched, shard["id"]))
        best = max(score for score, _, _ in scored)
        if best == 0:
            continue
        tied = [(matched, sid) for score, matched, sid in scored if score == best]
        if len(tied) < 2:
            continue

        tied_cells += 1
        if len({matched for matched, _ in tied}) == 1:
            single_facet_set += 1

        values = [impact_by_shard[sid] for _, sid in tied if impact_by_shard[sid]]
        if len(values) >= 2:
            comparable += 1
            spread = max(values) / min(values)
            spreads.append(spread)
            if spread < 1.25:
                narrow_spread += 1

    def share(numerator, denominator):
        return (numerator / denominator) if denominator else 0.0

    facet_share = share(single_facet_set, tied_cells)
    spread_share = share(narrow_spread, comparable)
    return {
        "tied_cells": tied_cells,
        "single_facet_set": single_facet_set,
        "single_facet_set_share": facet_share,
        "comparable_cells": comparable,
        "narrow_spread": narrow_spread,
        "narrow_spread_share": spread_share,
        "median_spread": sorted(spreads)[len(spreads) // 2] if spreads else None,
        "declines_on_facets": facet_share > 0.50,
        "declines_on_values": spread_share > 0.50,
        "verdict": "decline" if (facet_share > 0.50 or spread_share > 0.50) else "proceed",
    }
