"""What is a published figure actually made of?

Every shard's per-event impact is a beta-PERT over three anchors, and every anchor
declares the population it was measured on. Both halves have been published for
months — the anchors on the item's face, the corpus-wide bridging count in the
headline — and nothing has ever put them together. So a reader can see that a figure
rests on a Latitude breach and, separately, that 7 of 66 parameters across the whole
corpus are measured on the cell they are used for, without any way to learn that
**95% of this shard's impact mean rests on one anchor that was measured on neither its
size band nor its threat.**

That sentence is what this module computes.

**The partition is an identity, not an estimate.** `engine.tail_sensitivity` already
established that the engine's beta-PERT at the default confidence has mean
`(min + 4*likely + max) / 6`, so each anchor's contribution is exactly
`coefficient * value / (min + 4*likely + max)`. No seed, no trials, no Monte Carlo
error, and a reader can check it on paper. That property is the point: a disclosure a
reader has to trust is not much of a disclosure.

**It partitions the scenario, not the evidence card, and the difference is real.**
A calibration may transform an evidence value before the engine sees it — the AU
ransomware shard's `impact.likely` is a Sophos figure of **USD 650,000** on its card
and **AUD 900,000** in the scenario, via a declared `currency_convert` with
`round_to: 10000`. Partitioning card values would produce a breakdown of a number
nobody published. The values here are the ones the simulation runs, so the shares
compose the figure on the page; the *declarations* still come from the evidence
records, joined per parameter, because that is where the measured population lives.

**Families are partitioned separately and never blended.** The annual figure is the
product of a frequency mean and an impact mean, so there is no honest single
percentage for it — a share of a product is not the product of shares. Reporting the
pair is also the only reading consistent with [ADR-0011](../docs/adr/0011-fit-is-a-facet-set.md),
which refused a composite fit score twice because a mismatch fatal to one analysis is
irrelevant to the next.

**Bridged is not one thing, and collapsing it would make this useless.** An anchor
declared `industries: ['all']` was measured across a population that *includes* this
shard's industry; an anchor declared `countries: ['US']` used on an Australian shard
was measured somewhere else. Both are bridged under
[ADR-0003](../docs/adr/0003-shared-impact-bridges.md)'s rule and they are not the same
warning. A reader told only "100% bridged" learns to distrust the number; a reader
told which facets, and whether the source was broader or elsewhere, learns what the
number can be used for. The second is the product. The first is just alarm.

**The facet shares overlap and must never be summed.** One anchor bridged on both size
and threat contributes its whole share to each. They answer *"how much of this mean
rests on something not measured on my size band?"*, asked once per facet.
"""
from engine.cell_coverage import WILDCARDS
from engine.fair_calc import SCHEMA_PATH, load_and_validate, load_schema
from engine.provenance import build_module_provenance
from engine.risk_modules import find_risk_module
from engine.tail_sensitivity import PERT_CONFIDENCE, pert_mean

#: Facet keys as `engine.provenance` emits a module cell — note `company_size`, where
#: the explorer payload and `engine.cell_coverage` say `size`. Same facet, two spellings.
FACETS = (("country", "countries"), ("industry", "industries"),
          ("company_size", "company_size_bands"), ("threat", "threats"))

#: The beta-PERT weights, in the order the mean identity composes them.
COEFFICIENTS = {"min": 1, "likely": PERT_CONFIDENCE, "max": 1}
SLOTS = ("min", "likely", "max")
FAMILIES = ("frequency", "impact")


def classify(declared_for, cell):
    """Which of this cell's facets the declaration does not name, and why.

    Returns `(bridged_on, broader_on)`, following the engine's own rule exactly: a
    facet the cell sets, for which the declaration names values, none of which is the
    cell's value. `broader_on` is the subset where the declaration is a wildcard
    (`all`, `global`, `any`) — measured over a population containing this cell rather
    than over a different one.

    A facet the cell leaves unset is not tested, and a declaration naming no values
    for a facet is not evidence about it either way.
    """
    bridged, broader = [], []
    for facet, plural in FACETS:
        want = (cell or {}).get(facet)
        names = (declared_for or {}).get(plural) or []
        if not want or not names or want in names:
            continue
        bridged.append(facet)
        if set(names) & WILDCARDS:
            broader.append(facet)
    return bridged, broader


def compose_family(values, cards, cell, family):
    """Partition one family's mean across its three anchors.

    Returns None when the family is incomplete rather than partitioning what happens
    to be present: a share of an incomplete range is a different quantity wearing the
    same label.
    """
    if not values or any(values.get(slot) is None for slot in SLOTS):
        return None
    total = sum(COEFFICIENTS[slot] * values[slot] for slot in SLOTS)
    if not total:
        return None

    anchors = []
    for slot in SLOTS:
        card = cards.get(f"{family}.{slot}") or {}
        bridged, broader = classify(card.get("declared_for"), cell)
        anchors.append({
            "slot": slot,
            "parameter": f"{family}.{slot}",
            "value": values[slot],
            "share": COEFFICIENTS[slot] * values[slot] / total,
            "measured_here": not bridged,
            "bridged_on": bridged,
            "broader_on": broader,
            "elsewhere_on": [f for f in bridged if f not in broader],
            "basis": card.get("measurement_basis"),
            "source_name": card.get("source_name"),
            "evidence_id": card.get("evidence_id"),
            # The card's own value, kept so a transformed anchor is visible as one.
            "evidence_value": card.get("value"),
        })

    measured = sum(a["share"] for a in anchors if a["measured_here"])
    return {
        "family": family,
        "mean": pert_mean(values["min"], values["likely"], values["max"]),
        "anchors": anchors,
        "measured_share": measured,
        "bridged_share": 1.0 - measured,
        # Asked once per facet; these overlap and do not sum to bridged_share.
        "bridged_by_facet": {
            facet: sum(a["share"] for a in anchors if facet in a["bridged_on"])
            for facet, _ in FACETS
        },
        "dominant": max(anchors, key=lambda a: a["share"]),
    }


def compose_module(root, module_id):
    """Both families for one shard, with the annual figure deliberately left unsplit."""
    module = find_risk_module(module_id, root)
    scenario_path = root / (module.get("artifacts") or {})["scenario"]
    config = load_and_validate(scenario_path, load_schema(SCHEMA_PATH))
    provenance = build_module_provenance(module_id, root)
    cards = {card["parameter"]: card for card in provenance["cards"]}
    cell = provenance["cell"]

    families = {}
    for family in FAMILIES:
        composed = compose_family(config.get(family), cards, cell, family)
        if composed:
            families[family] = composed

    return {
        "module_id": module_id,
        "cell": cell,
        "currency": (config.get("metadata") or {}).get("currency"),
        "families": families,
        # Stated rather than computed: the annual mean is a product of the two family
        # means, so it has no single composition share. The pair is the answer.
        "annual_mean": (families["frequency"]["mean"] * families["impact"]["mean"]
                        if len(families) == len(FAMILIES) else None),
    }
