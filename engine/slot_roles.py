"""Anchor slot roles: does an anchor's measured quantity play the role its slot requires?

ADR-0007 (`coherence.py`) asks whether a family's anchors measure the *same* quantity.
ADR-0008 asks what a maximum *bounds*. This module asks the third question about the
same declared field: the beta-PERT the engine composes takes a floor, a **mode** and a
ceiling — so does the statistic we pass into each slot actually play that role?

For the mode slot the answer is structural, and it is no. **No value in the
`measurement_basis` vocabulary denotes a mode.** All eighteen name means, medians,
components, prevalences, ceilings, single observations or estimates. So no anchor in any
shard can correctly occupy the `likely` slot, and `MODAL_BASES` below is deliberately
empty rather than merely unpopulated.

Two readings follow, and both are published:

- **Every** `impact.likely` is something other than a calibrated mode.
- Of those, the ones carrying a **central-tendency statistic** — a published mean or
  median — are the sharper case, because a mean and a mode of a right-skewed loss
  distribution are different numbers with different meanings, and ordering two central
  tendencies by magnitude does not turn the smaller into a floor and the larger into a
  mode.

The same question applies to the floor slot, but only narrowly: a cost *component* is a
defensible lower bound on a total, whereas a central tendency is not a minimum by any
reading. Only the latter is declared here.

**This module declares; it does not repair.** No source consulted publishes a mode, and
the vocabulary cannot express one, so inventing a value to fill the slot is precisely the
move ADR-0009 forbids. Saying so on the record is the whole fix, and it moves no number.

Scope: impact families, which is what was measured
(`docs/internal/anchor_slot_inventory.md`). Whether frequency and loss-stage families
have the same defect is **unmeasured** — recorded here so its absence is not read as a
clean bill.
"""

from engine.coherence import ANCHORS, NON_RANGE_PREFIXES

#: Bases that denote a mode. Empty by inspection of the schema vocabulary, not by
#: oversight: nothing in `measurement_basis` names a most-likely single value.
MODAL_BASES = frozenset()

#: Published central tendencies. A mean is not a mode and it is not a minimum.
CENTRAL_TENDENCY_BASES = frozenset({"mean_total_event_cost", "median_total_event_cost"})

#: Families this module assesses. See the scope note above.
ASSESSED_FAMILIES = ("impact",)


def _split(parameter):
    """`impact.likely` -> ('impact', 'likely'). Returns (None, None) for non-anchors."""
    if not parameter:
        return None, None
    parts = parameter.split(".")
    if parts[-1] not in ANCHORS or parts[0] in NON_RANGE_PREFIXES:
        return None, None
    return ".".join(parts[:-1]), parts[-1]


def _readable(basis):
    return (basis or "undeclared").replace("_", " ")


def slot_declarations(module_provenance):
    """Slot-role declarations for one shard, in parameter order.

    Returns a list of `{parameter, family, anchor, basis, kind, declaration}` where
    `kind` is `mode_slot` or `floor_slot`. An anchor with no declaration is omitted.
    """
    out = []
    for card in module_provenance.get("cards", []):
        parameter = card.get("parameter") or ""
        family, anchor = _split(parameter)
        if not family or family not in ASSESSED_FAMILIES:
            continue
        basis = card.get("measurement_basis")
        if not basis:
            continue

        if anchor == "likely" and basis not in MODAL_BASES:
            central = basis in CENTRAL_TENDENCY_BASES
            if central:
                headline = (
                    f"`{parameter}` is a published {_readable(basis)}, not a calibrated mode"
                )
                detail = (
                    "it is a central-tendency statistic and the engine composes it as the mode "
                    "of a beta-PERT. No source held for this shard publishes a mode, and no "
                    "value in the declared measurement vocabulary denotes one, so this is "
                    "stated rather than corrected: the number is what its source measured, and "
                    "the slot is the engine's, not the source's."
                )
            else:
                headline = (
                    f"`{parameter}` is a published {_readable(basis)}, not a calibrated mode"
                )
                detail = (
                    "the engine composes it as the mode of a beta-PERT. No value in the declared "
                    "measurement vocabulary denotes a mode, so no anchor can occupy this slot "
                    "correctly."
                )
            out.append({"parameter": parameter, "family": family, "anchor": anchor,
                        "basis": basis, "kind": "mode_slot", "central_tendency": central,
                        "headline": headline, "detail": detail,
                        "declaration": f"{headline} — {detail}"})

        elif anchor == "min" and basis in CENTRAL_TENDENCY_BASES:
            headline = (
                f"`{parameter}` is a published {_readable(basis)}, not an observed minimum"
            )
            detail = (
                "it is a central-tendency statistic and the engine composes it as the floor of "
                "a beta-PERT. Half the measured population sits below a median, and a great "
                "deal of it sits below a mean, so this floor is not a lower bound on loss."
            )
            out.append({"parameter": parameter, "family": family, "anchor": anchor,
                        "basis": basis, "kind": "floor_slot", "central_tendency": True,
                        "headline": headline, "detail": detail,
                        "declaration": f"{headline} — {detail}"})
    return out


def build_portfolio_slot_roles(root, module_ids=None):
    """Slot-role declarations for every shard, plus portfolio totals."""
    from engine.provenance import build_portfolio_provenance

    portfolio = build_portfolio_provenance(root, module_ids=module_ids)
    modules = []
    mode_slot = mode_slot_central = floor_slot = 0
    for module_provenance in portfolio.get("modules", []):
        declarations = slot_declarations(module_provenance)
        for d in declarations:
            if d["kind"] == "mode_slot":
                mode_slot += 1
                if d["central_tendency"]:
                    mode_slot_central += 1
            else:
                floor_slot += 1
        modules.append({
            "module_id": module_provenance.get("module_id"),
            "title": module_provenance.get("title"),
            "declarations": declarations,
        })
    shards = len(modules)

    def _shards_with(kind, central=None):
        return sum(
            1 for m in modules
            if any(d["kind"] == kind and (central is None or d["central_tendency"] == central)
                   for d in m["declarations"])
        )

    return {
        "modules": modules,
        "totals": {
            "shards": shards,
            "mode_slot_declarations": mode_slot,
            "mode_slot_central_tendency": mode_slot_central,
            "floor_slot_declarations": floor_slot,
            "shards_mode_slot": _shards_with("mode_slot"),
            "shards_mode_slot_central_tendency": _shards_with("mode_slot", central=True),
            "shards_floor_slot": _shards_with("floor_slot"),
        },
    }
