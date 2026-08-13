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


def _card_population(record, cell_country):
    """ADR-0003: is this card's evidence drawn from the shard's own cell?

    Combines two layers: the record's stored `population_match` (specific declared
    applicability beyond the source's measured population) and a country-strict
    consumption check — a record whose applicability does not name the shard's own
    country (a global survey, or a foreign declaration reached via direct
    calibration reference) is bridged on country for this shard, whatever it
    honestly declared. Sector/size/threat come from the stored layer only:
    honest wildcard declarations are dilution, carried by the caveat, not borrowing.
    """
    pm = record.get("population_match") or {}
    dims = set(pm.get("bridged_on") or [])
    countries = (record.get("applicability") or {}).get("countries") or []
    if cell_country and cell_country not in countries:
        dims.add("country")
    return {"status": "bridged" if dims else "matched", "bridged_on": sorted(dims)}


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
    cell_country = ((module or {}).get("context") or {}).get("country")
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
                    "population": _card_population(record, cell_country),
                    "measurement_basis": record.get("measurement_basis"),
                    # ADR-0008: only ever set on an impact maximum, by schema rule.
                    "exceedance_basis": record.get("exceedance_basis"),
                    "exceedance_detail": record.get("exceedance_detail"),
                }
            )
        cards.append(card)
    return {"module_id": pack.get("module_id", module_id), "title": pack.get("title"), "cards": cards}


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
        lines.append("| Parameter | Value | Status | Measures | Exceedance | Source | Caveat |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for c in m["cards"]:
            source = c.get("source_name") or "—"
            if c.get("publication_date"):
                source += f" ({c['publication_date']})"
            caveat = (c.get("caveat") or "—").replace("|", "\\|").replace("\n", " ")
            status = c.get("status") or "—"
            pop = c.get("population") or {}
            if pop.get("status") == "bridged":
                status += f" (bridged: {', '.join(pop.get('bridged_on') or [])})"
            basis = c.get("measurement_basis") or "—"
            # ADR-0008: only maxima carry this, so every other row reads "—".
            exceedance = f"`{c['exceedance_basis']}`" if c.get("exceedance_basis") else "—"
            lines.append(
                f"| `{c['parameter']}` | {_fmt_value(c)} | {status} | `{basis}` | {exceedance} "
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
