"""Challenge-a-number provenance cards.

Every model parameter in a shard should be defensible *and* disputable in one
look: the chosen value, the named public source and the exact line it came from,
the confidence, and the caveat that limits it. This module assembles that card
per parameter from the shard's evidence records, and generates a pre-filled
"dispute this evidence" GitHub issue so a skeptic becomes a contributor.

It reads only real evidence-record fields; it never invents a value or a caveat.
"""
import urllib.parse

from engine.evidence_packs import (
    build_evidence_pack,
    find_risk_module,
    load_module_evidence_records,
)

# Repo slug for dispute links; overridden by the caller from `git remote`.
DEFAULT_REPO_SLUG = "raviaxo/RiskShard"


def repo_slug_from_remote(remote_url):
    """Derive `owner/name` from a git remote URL, or '' if it can't be parsed."""
    if not remote_url:
        return ""
    url = remote_url.strip()
    url = url[:-4] if url.endswith(".git") else url
    if url.startswith("git@"):  # git@github.com:owner/name
        _, _, path = url.partition(":")
        return path
    parts = url.split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else ""


def module_cell(module):
    """The target a shard's fit is computed against (ADR-0011).

    Fit only exists relative to a target, and ours is the shard's own cell. Naming
    it explicitly is what stops a derived, target-specific value from reading as a
    property of the evidence record.
    """
    ctx = (module or {}).get("context") or {}
    return {
        "country": ctx.get("country"),
        "industry": ctx.get("industry"),
        "company_size": ctx.get("company_size"),
        "threat": (module or {}).get("threat"),
    }


def _declared_for(record):
    """ADR-0011: the cells this record is declared usable in, as it declares them.

    Target-independent and required on every record, so it is the raw material a
    consumer needs to compute distance against *their* cell — which is why it is
    surfaced above the derived fit rather than left behind it.

    **It is not the observed population**, and ADR-0011 said it was. Measured
    2026-08-14: 17 of 141 records declare a narrow value on a facet their own
    `population_match.bridged_on` says the source did not measure — the IC3/Census
    BEC floor declares `financial_services` / `mid_market` while the numerator and
    denominator are both economy-wide. Labelling this field "measured on" would
    publish a fresh false claim while retiring an old one. What the source actually
    measured is recoverable only as the gap between this declaration and
    `not_measured_on` below; no field states it directly.
    """
    applicability = record.get("applicability") or {}
    return {
        "countries": list(applicability.get("countries") or []),
        "industries": list(applicability.get("industries") or []),
        "company_size_bands": list(applicability.get("company_size_bands") or []),
        "threats": list(applicability.get("threats") or []),
    }


def _not_measured_on(record):
    """The facets where the source's population is broader than the declaration.

    This is the record's *stored* `population_match.bridged_on` and nothing else. It
    is a property of the record — true for every reader, target or no target — and
    must not be folded into a "fit vs our cell" statement. Doing so would be the same
    error ADR-0011 corrects, pointed the other way.
    """
    return sorted((record.get("population_match") or {}).get("bridged_on") or [])


def _card_population(record, cell_country):
    """ADR-0003: is this card's evidence drawn from the shard's own cell?

    Combines two layers: the record's stored `population_match` (specific declared
    applicability beyond the source's measured population) and a country-strict
    consumption check — a record whose applicability does not name the shard's own
    country (a global survey, or a foreign declaration reached via direct
    calibration reference) is bridged on country for this shard, whatever it
    honestly declared. Sector/size/threat come from the stored layer only:
    honest wildcard declarations are dilution, carried by the caveat, not borrowing.

    ADR-0011: the result is a computation against *our* cell, not an attribute of
    the record. Every renderer must name the target it was computed against — see
    `format_fit`.

    Note that only the country layer is target-relative; the stored layer is
    intrinsic. `cell_mismatch()` recovers the split. This merge is left exactly as
    it was: it feeds the published cell-matched / bridged / cross-country counts,
    and this objective moves labels, not numbers.
    """
    pm = record.get("population_match") or {}
    dims = set(pm.get("bridged_on") or [])
    countries = (record.get("applicability") or {}).get("countries") or []
    if cell_country and cell_country not in countries:
        dims.add("country")
    return {"status": "bridged" if dims else "matched", "bridged_on": sorted(dims)}


def format_cell(cell):
    """A shard cell as one line: `US · finance · mid_market · bec`."""
    ordered = [
        (cell or {}).get("country"),
        (cell or {}).get("industry"),
        (cell or {}).get("company_size"),
        (cell or {}).get("threat"),
    ]
    return " · ".join(str(v) for v in ordered if v) or "an unstated target"


def cell_mismatch(card):
    """The target-relative half of a card's fit: facets bridged *because of our cell*.

    The merged `population` is two layers (see `_card_population`). Subtracting the
    record-intrinsic layer leaves only what changes when the target changes — which
    is the only part a reader with a different cell should recompute.
    """
    merged = set(((card.get("population") or {}).get("bridged_on")) or [])
    return sorted(merged - set(card.get("not_measured_on") or []))


def format_declared_for(declared_for):
    """The declared applicability as one line, facet by facet (ADR-0011).

    Never compressed to a score: the facets are listed so a reader decides which
    mismatches bite for their scenario, which is not a judgment we can make for them.
    """
    if not declared_for:
        return "—"
    labels = (
        ("countries", "countries"),
        ("industries", "industries"),
        ("sizes", "company_size_bands"),
        ("threats", "threats"),
    )
    parts = [
        f"{label} {', '.join(str(v) for v in declared_for.get(key) or [])}"
        for label, key in labels
        if declared_for.get(key)
    ]
    return " · ".join(parts) or "—"


def format_not_measured_on(not_measured_on):
    """The record-intrinsic gap: facets the source did not measure specifically."""
    if not not_measured_on:
        return "nothing — the source measured the cell it is declared for"
    return ", ".join(not_measured_on)


def format_fit(card, cell):
    """The target-relative half of the fit, stated against the target it assumes.

    ADR-0011: fit is a function of two things and we only own one, so it is never
    rendered without naming the other. Only the facets in `cell_mismatch` belong
    here — the rest is a property of the record and is rendered separately.
    """
    population = card.get("population")
    if not population:
        return "—"
    target = format_cell(cell)
    mismatch = cell_mismatch(card)
    if mismatch:
        return f"bridged vs {target} — on {', '.join(mismatch)}"
    return f"no mismatch vs {target} — which is our target, not yours"


def _calibration_selected_evidence(module, root):
    """Map parameter -> evidence_id as the module's calibration profile selects it.

    The card must display the record the simulation actually uses. The evidence
    pack's `best_evidence_id` ranks candidates by confidence-then-id, which can
    disagree with the calibration's explicit `evidence_id` whenever a parameter
    carries more than one record (found 2026-08-02: a superseded record kept "for
    reference" sorted first and the public card displayed evidence the calibration
    did not use). The calibration profile is the authority; the pack ranking is
    only a fallback for parameters the calibration does not name.
    """
    import yaml

    calibration_path = ((module or {}).get("artifacts") or {}).get("calibration")
    if not calibration_path:
        return {}
    try:
        profile = yaml.safe_load((root / calibration_path).read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    selected = {}
    for block, entries in (profile.get("parameters") or {}).items():
        for bound, spec in (entries or {}).items():
            evidence_id = (spec or {}).get("evidence_id")
            if evidence_id:
                selected[f"{block}.{bound}"] = evidence_id
    return selected


def build_module_provenance(module_id, root, feeds_by_id=None):
    """One provenance card per direct parameter of a shard, in parameter order.

    Each card carries the chosen value + unit, source identity, the cited line,
    the caveat (record `limitations`), confidence, and status. The record shown is
    the one the module's calibration profile selects for that parameter — what the
    simulation actually uses — falling back to the evidence pack's ranking only
    when the calibration does not name one. Parameters whose record can't be found
    still yield a card marked `missing` so a gap is visible, never silently dropped.
    """
    module = find_risk_module(module_id, root)
    pack = build_evidence_pack(module, root, feeds_by_id=feeds_by_id)
    records_by_id = {r["id"]: r for r in load_module_evidence_records(module, root)}
    cell = module_cell(module)
    cell_country = cell["country"]
    calibration_selected = _calibration_selected_evidence(module, root)

    cards = []
    for dp in pack.get("direct_parameters", []):
        selected_id = calibration_selected.get(dp.get("parameter"))
        if selected_id not in records_by_id:
            selected_id = dp.get("best_evidence_id")
        record = records_by_id.get(selected_id)
        card = {
            "parameter": dp.get("parameter"),
            "status": dp.get("status"),
            "confidence": (record or {}).get("confidence", dp.get("best_confidence")),
            "evidence_id": selected_id,
        }
        if record is None:
            card.update(
                {
                    "value": None,
                    "unit": None,
                    "source_name": None,
                    "source_type": None,
                    "source_citation": None,
                    "publication_date": None,
                    "cited_line": None,
                    "caveat": None,
                    "resolved": False,
                    "declared_for": None,
                    "not_measured_on": None,
                    "population": None,
                    "measurement_basis": None,
                    "exceedance_basis": None,
                    "exceedance_detail": None,
                }
            )
        else:
            card.update(
                {
                    "value": record.get("value"),
                    "unit": record.get("unit"),
                    "title": record.get("title"),
                    "source_name": record.get("source_name"),
                    "source_type": record.get("source_type"),
                    "source_citation": record.get("source_url_or_citation"),
                    "publication_date": record.get("publication_date"),
                    "cited_line": record.get("citation_detail"),
                    "caveat": record.get("limitations"),
                    "resolved": True,
                    # ADR-0011, in the order a reader should meet them. The first
                    # two are properties of the record and true for everyone; only
                    # the merged `population` depends on the `cell` below.
                    "declared_for": _declared_for(record),
                    "not_measured_on": _not_measured_on(record),
                    "population": _card_population(record, cell_country),
                    "measurement_basis": record.get("measurement_basis"),
                    # ADR-0008: only ever set on an impact maximum, by schema rule.
                    "exceedance_basis": record.get("exceedance_basis"),
                    "exceedance_detail": record.get("exceedance_detail"),
                }
            )
        cards.append(card)
    return {
        "module_id": pack.get("module_id", module_id),
        "title": pack.get("title"),
        # The target every card's `population` was computed against (ADR-0011).
        # Held once per module rather than copied onto each card.
        "cell": cell,
        "cards": cards,
    }


def build_portfolio_provenance(root, module_ids=None):
    """Provenance for every shard (or a given subset), for a whole-portfolio audit.

    Returns {'modules': [<build_module_provenance result>, ...], 'totals': {...}} where
    totals count parameters by status across the portfolio — the one-glance answer to
    "how much of this system is source-backed?".
    """
    from engine.risk_modules import search_risk_modules

    if module_ids is None:
        module_ids = [m.get("id") for m in search_risk_modules("", root)]
    modules = [build_module_provenance(mid, root) for mid in module_ids]

    source_backed = bridged = missing = total = 0
    cell_matched = cross_cell = cross_country = 0
    for m in modules:
        for c in m["cards"]:
            total += 1
            if c.get("status") == "source_backed":
                source_backed += 1
                # ADR-0003 part 2: split the headline so "source-backed" stops
                # implying cell-specificity it cannot verify.
                pop = c.get("population") or {}
                if pop.get("status") == "bridged":
                    cross_cell += 1
                    if "country" in (pop.get("bridged_on") or []):
                        cross_country += 1
                else:
                    cell_matched += 1
            elif c.get("resolved"):
                bridged += 1
            else:
                missing += 1
    return {
        "modules": modules,
        "totals": {
            "shards": len(modules),
            "params_total": total,
            "params_source_backed": source_backed,
            "params_cell_matched": cell_matched,
            "params_cross_cell": cross_cell,
            "params_cross_country": cross_country,
            "params_bridged": bridged,
            "params_missing": missing,
        },
    }


def _impact_anchors(module_provenance):
    """The shard's three impact anchors as the cards report them, or None if incomplete.

    Uses the calibration-selected cards rather than re-reading the scenario, so this
    stays consistent with everything else in the report.
    """
    found = {}
    for card in module_provenance.get("cards", []):
        parameter = card.get("parameter") or ""
        if parameter in ("impact.min", "impact.likely", "impact.max"):
            found[parameter.split(".")[1]] = card.get("value")
    if set(found) != {"min", "likely", "max"} or any(v is None for v in found.values()):
        return None
    return found


def format_portfolio_markdown(portfolio):
    """A single shareable evidence report: every number, its source, and its caveat.

    This is the whole-system "answers nobody can rebut" artifact — one document where
    every model input is traceable to a named public source or labeled honestly.
    """
    from engine.coherence import module_coherence  # local: coherence imports this module

    t = portfolio["totals"]
    # ADR-0011: how much of the bridged headline is actually about our target.
    # Derived here rather than stored, so it cannot disagree with the rows below it.
    bridged_cards = [
        c for m in portfolio["modules"] for c in m["cards"]
        if (c.get("population") or {}).get("status") == "bridged"
    ]
    bridged_target_relative = sum(1 for c in bridged_cards if cell_mismatch(c))
    bridged_intrinsic = len(bridged_cards) - bridged_target_relative
    coherence_by_module = {
        m["module_id"]: module_coherence(m) for m in portfolio["modules"]
    }
    all_families = [f for fams in coherence_by_module.values() for f in fams]
    coherent = sum(1 for f in all_families if f["status"] == "coherent")
    mixed = sum(1 for f in all_families if f["status"] == "mixed")

    # ADR-0008: the third axis, computed from the same cards.
    from engine.exceedance import module_exceedance
    from engine.tail_sensitivity import LEVERAGE_CONCERN, max_leverage

    exceedance_by_module = {m["module_id"]: module_exceedance(m) for m in portfolio["modules"]}

    # The anchor-slot declaration: does each anchor's measured quantity play the
    # statistical role its slot requires? Derived from the same cards.
    from engine.slot_roles import slot_declarations

    slots_by_module = {m["module_id"]: slot_declarations(m) for m in portfolio["modules"]}
    all_slots = [d for ds in slots_by_module.values() for d in ds]
    slot_mode = [d for d in all_slots if d["kind"] == "mode_slot"]
    slot_mode_ct = [d for d in slot_mode if d["central_tendency"]]
    slot_floor = [d for d in all_slots if d["kind"] == "floor_slot"]
    # Commitment 2: the maximum's share of the modeled mean, from the same anchors the
    # cards already carry — no scenario read and no simulation needed here.
    leverage_by_module = {
        m["module_id"]: max_leverage(_impact_anchors(m)) for m in portfolio["modules"]
    }
    all_maxima = [e for maxima in exceedance_by_module.values() for e in maxima]
    exc = {
        "maxima": len(all_maxima),
        "quantified": sum(1 for e in all_maxima if e["quantified"]),
        "by_basis": {
            basis: sum(1 for e in all_maxima if e["exceedance_basis"] == basis)
            for basis in ("modeled_quantile", "observed_rank", "population_ceiling", "none_known")
        },
    }

    lines = [
        "# RiskShard Evidence Report",
        "",
        "Every model parameter in every shard, with the source it traces to and the "
        "caveat that limits it. Generated from the governed evidence — nothing here is "
        "hand-written. Dispute any row: `riskshard_modules.py provenance <shard> --dispute <param>`.",
        "",
        f"**Portfolio:** {t['shards']} shards · {t['params_source_backed']} of "
        f"{t['params_total']} parameters source-backed — {t.get('params_cell_matched', 0)} "
        f"cell-matched, {t.get('params_cross_cell', 0)} bridged (of which "
        f"{t.get('params_cross_country', 0)} cross-country) · {t['params_bridged']} "
        f"bridged/estimated · {t['params_missing']} missing. A bridged parameter is "
        "source-backed by evidence not drawn from the shard's own cell (ADR-0003); "
        "the dimension borrowed across is named per row.",
        "",
        "**Fit is relative to a target, and the target here is ours (ADR-0011).** Three columns "
        "carry what used to be one. *Declared for* is the cell the record declares itself usable "
        "in. *Not measured on* names the facets where the source's own population is broader than "
        "that declaration — the IC3/Census BEC floor is declared for financial-services "
        "mid-market firms, but its numerator and denominator are both economy-wide, so it reads "
        "`sector, size`. Both are properties of the record and true for every reader. Only *Fit "
        "vs this cell* depends on a target, and the target is **this shard's cell**, named above "
        "each table — it is what you would recompute against yours, and nothing else in the row "
        "changes when you do.",
        "",
        f"**That split is worth a number.** Of the {len(bridged_cards)} parameters labelled "
        f"*bridged*, **{bridged_intrinsic} are bridged for a reason intrinsic to the record** — "
        "the source measured a broader population than the record declares — which is as true for "
        f"you as for us. Only **{bridged_target_relative}** are bridged because of *our* cell. The "
        "headline count is unchanged and still correct; what it means is now separable.",
        "",
        "**A correction this reporting produced.** ADR-0011 asserted that `applicability` is the "
        "observed population. It is not: 17 of 141 records declare a narrow value on a facet "
        "their own `population_match` says the source did not measure. Publishing that field as "
        "*measured on* would have replaced one mislabel with another, so it is published as "
        "*declared for* and the gap is given its own column. **No source publishes the observed "
        "population as a field and we have not invented one.** None of these columns is ever "
        "summarised into a score, grade or percentage: compressing them would assert that a "
        "geography mismatch and a size mismatch trade off against each other in a way we cannot "
        "know for your scenario. A geography mismatch is fatal to one analysis and irrelevant to "
        "the next, and only you know which.",
        "",
        f"**Range coherence:** {coherent} coherent · {mixed} mixed of "
        f"{len(all_families)} parameter families. A *mixed* range composes anchors that "
        "measure different quantities — each validly sourced, but not readings of the same "
        "thing (ADR-0007). Read this together with the line above: population match and "
        "measurement basis are independent, and a fully cell-matched parameter can still "
        "sit in a mixed range. The basis of every anchor is named per row.",
        "",
        f"**Tail exceedance:** {exc['quantified']} of {exc['maxima']} `impact.max` anchors "
        f"carry an exceedance statement — {exc['by_basis']['modeled_quantile']} modeled "
        f"quantiles, {exc['by_basis']['observed_rank']} observed ranks. "
        f"{exc['by_basis']['population_ceiling']} are legal ceilings and "
        f"{exc['by_basis']['none_known']} carry nothing at all (ADR-0008). A maximum here is "
        "*the largest loss we found*, not *the largest loss that can happen*, unless its row "
        "says otherwise — and the maximum is the anchor a simulated mean is most sensitive to.",
        "",
        f"**Anchor slot roles:** the engine composes each range as a beta-PERT, which needs a "
        f"floor, a **mode** and a ceiling. None of the {len(slot_mode)} `impact.likely` anchors "
        f"is a calibrated mode — no value in the declared measurement vocabulary denotes one — "
        f"and {len(slot_mode_ct)} of them are a published mean or median, a central-tendency "
        f"statistic standing in the mode slot. A further {len(slot_floor)} use a central "
        "tendency as the floor, which is not a lower bound on loss. This is declared and not "
        "corrected: no source consulted publishes a mode, and inventing one to fill the slot "
        "would be manufacturing data. It is a statement about the model's internal consistency "
        "and it implies nothing about whether the output is high or low.",
        "",
    ]
    for m in portfolio["modules"]:
        lines.append(f"## {m['module_id']}")
        title = m.get("title")
        if title:
            lines.append(f"_{title}_")
        lines.append("")
        # Name the target before the table that reports fit against it (ADR-0011).
        lines.append(f"**Fit below is computed against this cell:** {format_cell(m.get('cell'))}")
        lines.append("")
        for family in coherence_by_module.get(m["module_id"], []):
            if family["status"] == "mixed":
                lines.append(
                    f"> **`{family['family']}` is a mixed range** — its anchors measure "
                    f"{len(family['bases'])} different quantities: "
                    f"{', '.join('`' + b + '`' for b in family['bases'])}."
                )
                lines.append("")
        for d in slots_by_module.get(m["module_id"], []):
            lines.append(f"> **{d['headline']}** — {d['detail']}")
            lines.append("")
        # ADR-0008 commitment 2: analytic, so it costs no simulation to state here.
        leverage = leverage_by_module.get(m["module_id"])
        if leverage is not None and leverage >= LEVERAGE_CONCERN:
            lines.append(
                f"> **{leverage:.0%} of this shard's modeled loss comes from `impact.max` alone** "
                "— the distribution's mean is a weighted blend of the three impact anchors and the "
                "maximum carries most of that weight. Read it with the exceedance line below."
            )
            lines.append("")
        for entry in exceedance_by_module.get(m["module_id"], []):
            if entry["exceedance_basis"] == "none_known":
                lines.append(
                    f"> **`{entry['parameter']}` bounds nothing** — it carries no exceedance "
                    "probability (ADR-0008). It says a loss this size happened, not how often "
                    "a loss is worse. Treat it as the largest loss found, not the largest "
                    "possible."
                )
                lines.append("")
            elif entry["exceedance_detail"]:
                lines.append(
                    f"> **`{entry['parameter']}` exceedance** (`{entry['exceedance_basis']}`) — "
                    f"{entry['exceedance_detail']}"
                )
                lines.append("")
        lines.append(
            "| Parameter | Value | Status | Declared for | Not measured on "
            "| Fit vs this cell | Measures | Exceedance | Source | Caveat |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for c in m["cards"]:
            source = c.get("source_name") or "—"
            if c.get("publication_date"):
                source += f" ({c['publication_date']})"
            caveat = (c.get("caveat") or "—").replace("|", "\\|").replace("\n", " ")
            status = c.get("status") or "—"
            # ADR-0011: three separate columns, so the derived one cannot be read as
            # intrinsic and the intrinsic ones cannot be read as target-relative.
            declared_for = format_declared_for(c.get("declared_for"))
            not_measured = (
                ", ".join(c["not_measured_on"]) if c.get("not_measured_on")
                else ("—" if c.get("not_measured_on") is None else "nothing")
            )
            mismatch = cell_mismatch(c) if c.get("population") else []
            fit = ", ".join(mismatch) if mismatch else ("no mismatch" if c.get("population") else "—")
            basis = c.get("measurement_basis") or "—"
            # ADR-0008: only maxima carry this, so every other row reads "—".
            exceedance = f"`{c['exceedance_basis']}`" if c.get("exceedance_basis") else "—"
            lines.append(
                f"| `{c['parameter']}` | {_fmt_value(c)} | {status} | {declared_for} "
                f"| {not_measured} | {fit} | `{basis}` | {exceedance} "
                f"| {source.replace('|', chr(92) + '|')} | {caveat} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _fmt_value(card):
    if card.get("value") is None:
        return "(no source-backed value)"
    unit = f" {card['unit']}" if card.get("unit") else ""
    return f"{card['value']}{unit}"


def format_provenance(provenance, parameter=None):
    """Human-readable challenge cards. If `parameter` is given, only that one."""
    cards = provenance["cards"]
    if parameter:
        cards = [c for c in cards if c["parameter"] == parameter]
        if not cards:
            return f"No such parameter '{parameter}' in {provenance['module_id']}.\n"

    cell = provenance.get("cell")
    lines = [f"Provenance — {provenance['module_id']} ({provenance.get('title') or ''})".rstrip(), ""]
    for c in cards:
        badge = f"{c['status']} · confidence {c.get('confidence') or 'unrated'}"
        lines.append(f"{c['parameter']} = {_fmt_value(c)}   [{badge}]")
        if c.get("source_name"):
            pub = f", {c['publication_date']}" if c.get("publication_date") else ""
            lines.append(f"  Source : {c['source_name']} ({c.get('source_type') or 'source'}{pub})")
        if c.get("source_citation"):
            lines.append(f"  Cite   : {c['source_citation']}")
        if c.get("cited_line"):
            lines.append(f"  Quote  : {c['cited_line']}")
        # ADR-0011: the record's own declarations first, our fit against them last,
        # because only the last one changes when the reader's target does.
        if c.get("declared_for"):
            lines.append(f"  Declared for : {format_declared_for(c['declared_for'])}")
            lines.append(f"  Not measured on : {format_not_measured_on(c.get('not_measured_on'))}")
        if c.get("population"):
            lines.append(f"  Fit    : {format_fit(c, cell)}")
        if c.get("caveat"):
            lines.append(f"  Caveat : {c['caveat']}")
        lines.append(f"  Challenge it: add --dispute {c['parameter']} to open a pre-filled issue.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_dispute_issue(provenance, parameter):
    """A pre-filled GitHub issue (title + body) challenging one parameter's evidence."""
    card = next((c for c in provenance["cards"] if c["parameter"] == parameter), None)
    if card is None:
        raise ValueError(f"No such parameter '{parameter}' in {provenance['module_id']}")

    module_id = provenance["module_id"]
    title = f"Dispute: {module_id} / {parameter} = {_fmt_value(card)}"
    body = "\n".join(
        [
            f"**Shard:** `{module_id}`",
            f"**Parameter:** `{parameter}`",
            f"**Current value:** {_fmt_value(card)}",
            f"**Status / confidence:** {card.get('status')} / {card.get('confidence') or 'unrated'}",
            f"**Current evidence:** `{card.get('evidence_id') or '(none)'}`"
            + (f" — {card['source_name']}" if card.get("source_name") else ""),
            f"**Current caveat:** {card.get('caveat') or '(none recorded)'}",
            "",
            "### What I'm disputing",
            "_Which of the value, the source, or the caveat is wrong — and why._",
            "",
            "### Evidence I'm proposing instead",
            "_Named public source, the exact line, publication date, and how it "
            "maps to this parameter. A stronger or more specific source beats a "
            "broader one; label estimates as estimates._",
            "",
            "_Filed via `riskshard_modules.py provenance --dispute`. See "
            "CONTRIBUTING.md for the evidence bar._",
        ]
    )
    return {"title": title, "body": body}


def dispute_issue_url(repo_slug, issue):
    """A github.com new-issue URL with the title and body pre-filled."""
    slug = repo_slug or DEFAULT_REPO_SLUG
    query = urllib.parse.urlencode({"title": issue["title"], "body": issue["body"]})
    return f"https://github.com/{slug}/issues/new?{query}"
