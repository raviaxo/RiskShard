"""Tail exceedance: does a maximum say anything about being exceeded?

ADR-0008. Three declared axes now sit on every number the engine composes.
`population_match` (ADR-0003) answers *who was measured*. `measurement_basis`
(ADR-0007) answers *what quantity was measured*. This module reads the third:
**what, if anything, is known about the value being exceeded.**

It exists because measuring the second axis exposed the defect the first two
could not see. A maximum is the anchor a reader treats as the safe outer bound,
and it is also — measurably — the anchor the simulated mean is most sensitive to:
see `docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md`, where the per-event mean runs
14.8x its own mode because the maximum drives the distribution rather than
bounding it, and moving that one anchor swings P(event > AUD 20M) from 0% to 23%.

`none_known` is a legal value and, today, the common one. That is the point. It is
not a placeholder waiting to be cleared: published loss distributions with tail
quantiles are rare and mostly commercial. What the declaration buys is that a
reader stops mistaking *the largest loss we found* for *the largest loss that can
happen*.

Like coherence, this reads the **calibration-selected** anchors, because those are
the ones the simulation composes.
"""

from engine.provenance import build_portfolio_provenance

#: A maximum's exceedance vocabulary, weakest claim last.
BASES = ("modeled_quantile", "observed_rank", "population_ceiling", "none_known")

#: The bases that carry an actual exceedance statement a reader can act on.
QUANTIFIED = ("modeled_quantile", "observed_rank")

#: One-line reading of each basis, for surfaces that show it to a reader.
BASIS_MEANING = {
    "modeled_quantile": "a stated percentile of a fitted or published loss distribution",
    "observed_rank": "the k-th largest of N observations, so an empirical exceedance can be stated",
    "population_ceiling": "a legal or contractual bound — nothing exceeds it under that head of "
                          "loss, and it carries no information about likelihood",
    "none_known": "no exceedance statement is available — this is the largest loss found, "
                  "not the largest that can happen",
}

#: What a reader must be told when a maximum admits nothing about being exceeded.
NONE_KNOWN_WARNING = (
    "This maximum carries no exceedance probability: it says a loss this size happened, "
    "not how often a loss is worse."
)


def _is_impact_max(parameter):
    return bool(parameter) and parameter.split(".")[-2:] == ["impact", "max"]


def module_exceedance(module_provenance):
    """Every impact maximum in one shard, with its declared exceedance basis.

    Returns a list of dicts in parameter order:
    `{parameter, value, unit, measurement_basis, exceedance_basis, exceedance_detail,
      quantified, title}`.
    """
    out = []
    for card in module_provenance.get("cards", []):
        if not _is_impact_max(card.get("parameter")):
            continue
        basis = card.get("exceedance_basis")
        out.append(
            {
                "parameter": card.get("parameter"),
                "value": card.get("value"),
                "unit": card.get("unit"),
                "title": card.get("title"),
                "measurement_basis": card.get("measurement_basis"),
                "exceedance_basis": basis,
                "exceedance_detail": card.get("exceedance_detail"),
                "quantified": basis in QUANTIFIED,
            }
        )
    return out


def build_portfolio_exceedance(root, module_ids=None):
    """Exceedance for every shard's maxima, plus portfolio totals.

    Returns `{'modules': [{module_id, title, maxima: [...]}, ...], 'totals': {...}}`.
    `totals['by_basis']` counts each declared basis; `totals['undeclared']` counts maxima
    the schema should have caught (it requires the field) and is a defect if non-zero.
    """
    portfolio = build_portfolio_provenance(root, module_ids=module_ids)
    modules = []
    by_basis = {basis: 0 for basis in BASES}
    undeclared = 0
    for module_provenance in portfolio.get("modules", []):
        maxima = module_exceedance(module_provenance)
        for entry in maxima:
            basis = entry["exceedance_basis"]
            if basis in by_basis:
                by_basis[basis] += 1
            else:
                undeclared += 1
        modules.append(
            {
                "module_id": module_provenance.get("module_id"),
                "title": module_provenance.get("title"),
                "maxima": maxima,
            }
        )
    total = sum(by_basis.values()) + undeclared
    return {
        "modules": modules,
        "totals": {
            "maxima": total,
            "by_basis": by_basis,
            "undeclared": undeclared,
            "quantified": sum(by_basis[b] for b in QUANTIFIED),
            "none_known": by_basis["none_known"],
            "shards": len(modules),
            "shards_with_an_unquantified_max": sum(
                1
                for m in modules
                if any(not e["quantified"] for e in m["maxima"])
            ),
        },
    }


def headline(totals):
    """The one sentence a reader should leave with. Used by every surface."""
    return (
        f"{totals['quantified']} of {totals['maxima']} impact maxima carry an exceedance "
        f"statement; {totals['by_basis']['none_known']} carry none and "
        f"{totals['by_basis']['population_ceiling']} are legal ceilings. "
        f"{totals['by_basis']['modeled_quantile']} are modeled quantiles."
    )


def format_portfolio_markdown(portfolio):
    """Human-readable exceedance report, mirroring the coherence report's shape."""
    totals = portfolio["totals"]
    lines = [
        "# Tail exceedance report",
        "",
        "Does a shard's `impact.max` say anything about being exceeded?",
        "See [ADR-0008](adr/0008-the-governed-tail.md). `none_known` is a declaration, not a",
        "defect — it is the honest answer for most published evidence, and declaring it is",
        "what stops a reader reading an anecdote as a bound.",
        "",
        f"**{headline(totals)}**",
        "",
    ]
    if totals["undeclared"]:
        lines.append(
            f"{totals['undeclared']} maximum/maxima carry no declaration at all — the schema "
            "requires one, so this is a defect, not a state."
        )
        lines.append("")
    for module in portfolio["modules"]:
        lines.append(f"## {module['module_id']}")
        lines.append("")
        for entry in module["maxima"]:
            basis = entry["exceedance_basis"] or "undeclared"
            lines.append(
                f"- **`{entry['parameter']}`** {entry['value']} — `{basis}`: "
                f"{BASIS_MEANING.get(basis, 'undeclared')}"
            )
            if entry["exceedance_detail"]:
                lines.append(f"  - {entry['exceedance_detail']}")
            elif basis == "none_known":
                lines.append(f"  - {NONE_KNOWN_WARNING}")
        lines.append("")
    return "\n".join(lines)
