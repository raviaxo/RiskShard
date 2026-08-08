"""Range coherence: do a parameter family's anchors measure the same quantity?

ADR-0007. `population_match` (ADR-0003) answers *who was measured*. This module
answers *what was measured* — whether the `min`/`likely`/`max` anchors the engine
composes into one triangular distribution are readings of the same quantity.

A family is `coherent` when every selected anchor shares one `measurement_basis`,
and `mixed` when two or more bases appear. `mixed` is a declaration, not a verdict:
a median floor beneath a mean mode may well be defensible. What is not defensible
is it being invisible. Which mixes are acceptable is deliberately left open — see
the ADR's open questions.

Coherence reads the *calibration-selected* records, because those are the ones the
simulation composes. Context parameters are excluded: they never enter a range.
"""

from engine.provenance import build_portfolio_provenance

#: Parameter prefixes that are never composed into a distribution.
NON_RANGE_PREFIXES = ("context", "privacy_breach")

#: Anchor names, in the order a range is built.
ANCHORS = ("min", "likely", "max")


def _family_of(parameter):
    """`impact.max` -> `impact`; `loss_stage.regulatory_penalty.impact.min` -> its stage family."""
    if not parameter:
        return None, None
    parts = parameter.split(".")
    if parts[-1] not in ANCHORS:
        return None, None
    return ".".join(parts[:-1]), parts[-1]


def module_coherence(module_provenance):
    """Coherence status for each parameter family of one shard.

    Returns a list of dicts, one per family, in parameter order:
    `{family, status, bases, anchors: {min: {...}, ...}, unresolved: [...]}`.
    """
    families = {}
    order = []
    for card in module_provenance.get("cards", []):
        parameter = card.get("parameter") or ""
        if parameter.split(".")[0] in NON_RANGE_PREFIXES:
            continue
        family, anchor = _family_of(parameter)
        if not family:
            continue
        if family not in families:
            families[family] = {}
            order.append(family)
        families[family][anchor] = card

    results = []
    for family in order:
        anchors = families[family]
        bases = []
        unresolved = []
        for anchor in ANCHORS:
            card = anchors.get(anchor)
            if card is None:
                continue
            basis = card.get("measurement_basis")
            if not basis:
                unresolved.append(anchor)
                continue
            if basis not in bases:
                bases.append(basis)
        if unresolved or not bases:
            status = "undeclared"
        elif len(bases) == 1:
            status = "coherent"
        else:
            status = "mixed"
        results.append(
            {
                "family": family,
                "status": status,
                "bases": bases,
                "unresolved": unresolved,
                "anchors": {
                    anchor: {
                        "parameter": card.get("parameter"),
                        "value": card.get("value"),
                        "measurement_basis": card.get("measurement_basis"),
                        "exceedance_basis": card.get("exceedance_basis"),
                        "exceedance_detail": card.get("exceedance_detail"),
                        "title": card.get("title"),
                    }
                    for anchor, card in anchors.items()
                },
            }
        )
    return results


def build_portfolio_coherence(root, module_ids=None):
    """Coherence for every shard, plus portfolio totals.

    Returns `{'modules': [{module_id, title, families: [...]}, ...], 'totals': {...}}`.
    """
    portfolio = build_portfolio_provenance(root, module_ids=module_ids)
    modules = []
    coherent = mixed = undeclared = 0
    for module_provenance in portfolio.get("modules", []):
        families = module_coherence(module_provenance)
        for family in families:
            if family["status"] == "coherent":
                coherent += 1
            elif family["status"] == "mixed":
                mixed += 1
            else:
                undeclared += 1
        modules.append(
            {
                "module_id": module_provenance.get("module_id"),
                "title": module_provenance.get("title"),
                "families": families,
            }
        )
    total = coherent + mixed + undeclared
    return {
        "modules": modules,
        "totals": {
            "families": total,
            "coherent": coherent,
            "mixed": mixed,
            "undeclared": undeclared,
            "shards_with_a_mixed_family": sum(
                1 for m in modules if any(f["status"] == "mixed" for f in m["families"])
            ),
            "shards": len(modules),
        },
    }


def format_portfolio_markdown(portfolio):
    """Human-readable coherence report, mirroring the provenance report's shape."""
    totals = portfolio["totals"]
    lines = [
        "# Range coherence report",
        "",
        "Do a parameter family's `min`/`likely`/`max` anchors measure the same quantity?",
        "See [ADR-0007](adr/0007-construct-coherence.md). `mixed` is a declaration, not a",
        "verdict — the bases are named so a reader can judge for themselves.",
        "",
        f"**{totals['coherent']} coherent · {totals['mixed']} mixed** of {totals['families']} "
        f"parameter families across {totals['shards']} "
        f"{'shard' if totals['shards'] == 1 else 'shards'} "
        f"({totals['shards_with_a_mixed_family']} carry at least one mixed family).",
        "",
    ]
    if totals["undeclared"]:
        lines.append(f"{totals['undeclared']} family/families could not be assessed (undeclared basis).")
        lines.append("")
    for module in portfolio["modules"]:
        lines.append(f"## {module['module_id']}")
        lines.append("")
        for family in module["families"]:
            status = family["status"]
            marker = "coherent" if status == "coherent" else status
            lines.append(f"- **{family['family']}** — {marker}: {', '.join(family['bases']) or 'n/a'}")
            if status == "mixed":
                for anchor in ANCHORS:
                    info = family["anchors"].get(anchor)
                    if info:
                        lines.append(
                            f"  - `{anchor}` {info['value']} — {info['measurement_basis']}"
                        )
        lines.append("")
    return "\n".join(lines)
