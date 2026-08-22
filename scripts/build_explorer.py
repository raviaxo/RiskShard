#!/usr/bin/env python3
"""Build the public risk-shard explorer page from the repo's own governed data.

Regenerates docs/index.html (served by GitHub Pages) from:
  - provenance --all  : every parameter's value, source, cited line, and caveat
  - a real Monte Carlo run per shard : the AVG/P95/P99 loss range

Everything on the page is generated here — nothing is hand-written — so the
explorer is itself a reproducible, governed artifact rather than a one-off demo.
Re-run after any evidence change: `python scripts/build_explorer.py`.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.coherence import module_coherence  # noqa: E402
from engine.exceedance import module_exceedance  # noqa: E402
from engine.tail_sensitivity import LEVERAGE_CONCERN, max_leverage  # noqa: E402
from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.risk_modules import find_risk_module  # noqa: E402
from engine.slot_roles import slot_declarations  # noqa: E402
from engine.web_console import WebConsoleApp  # noqa: E402
from engine.composition import compose_module, payload as composition_payload

TEMPLATE = Path(__file__).resolve().parent / "explorer_template.html"
REPO_URL = "https://github.com/raviaxo/RiskShard"
REVISIONS_DIR = ROOT / "revisions"
ALIASES_PATH = ROOT / "aliases.yaml"
RELEASES_DIR = ROOT / "data_pack_releases"
# Where the built page is served. Absolute URLs are required by Open Graph /
# Twitter cards, so link previews resolve when the page is shared.
SITE_URL = "https://raviaxo.github.io/RiskShard/"


def _scenario_impact(root, module_id):
    """The impact range the simulation actually runs, straight from the scenario file.

    Read from the scenario rather than the calibration because the scenario carries the
    values the Monte Carlo composes — the same reason the drift gate compares the two.
    """
    module = find_risk_module(module_id, root) or {}
    scenario_path = root / ((module.get("artifacts") or {}).get("scenario") or "")
    if not scenario_path.is_file():
        return None
    scenario = yaml.safe_load(scenario_path.read_text(encoding="utf-8")) or {}
    return scenario.get("impact")


def _loss_range(app_root, module_id):
    """Run a real seeded simulation for one shard; return currency + AVG/P95/P99."""
    app = WebConsoleApp(root=app_root)
    app.run_command(f"use {module_id}")
    out = app.run_command("run")["output"]

    def grab(label):
        m = re.search(rf"^{label}\s*:\s*(.+)$", out, re.M)
        return m.group(1).strip() if m else None

    return {"currency": grab("Currency"), "avg": grab("AVG"), "p95": grab("P95"), "p99": grab("P99")}


def load_revisions(path=None):
    """Method changes that moved published numbers (not evidence changes).

    One file per revision rather than one shared list: a single newest-first YAML file
    meant every branch prepended to line 1 and collided with every other branch. Separate
    files merge silently.

    Newest first, by date then filename; same-day ordering is by filename and is not
    otherwise meaningful.
    """
    directory = Path(path or REVISIONS_DIR)
    if not directory.exists():
        return []
    entries = []
    for file_path in sorted(directory.glob("*.yaml"), reverse=True):
        entry = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        entries.append({
            "date": str(entry.get("date", "")),
            "title": entry.get("title", ""),
            "effect": (entry.get("effect") or "").strip(),
            "reason": (entry.get("reason") or "").strip(),
            "decision": entry.get("decision"),
            # Count of outright retractions this entry records (a figure withdrawn
            # because it appears in no primary source), as opposed to a value moved
            # by better evidence. Feeds the "numbers broken so far" tally.
            "retractions": int(entry.get("retractions") or 0),
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def latest_release(releases_dir=None):
    """The newest data-pack release id, used to pin citations (ADR-0004).

    Releases are immutable and fingerprinted, so pinning a citation to one lets a
    reader confirm years later that the value they cited is the value that was there.
    """
    directory = Path(releases_dir or RELEASES_DIR)
    if not directory.exists():
        return None
    artifacts = sorted(p for p in directory.glob("*.json"))
    if not artifacts:
        return None
    payload = json.loads(artifacts[-1].read_text(encoding="utf-8"))
    return payload.get("release_version") or artifacts[-1].stem


def load_aliases(path=None):
    """Old shard id -> current shard id (ADR-0004 permanence guarantee).

    A rename must not break a citation someone already wrote down, so retired ids
    keep resolving through this table rather than 404-ing.
    """
    path = Path(path or ALIASES_PATH)
    if not path.exists():
        return {}
    return {str(k): str(v) for k, v in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).items()}


def build_data(root):
    portfolio = build_portfolio_provenance(root)
    shards = []
    coherent = mixed = 0
    maxima_total = maxima_quantified = maxima_none_known = 0
    shards_tail_driven = 0
    for module in portfolio["modules"]:
        mid = module["module_id"]
        mod = find_risk_module(mid, root)
        ctx = (mod or {}).get("context", {})
        rng = _loss_range(root, mid)
        # ADR-0007: does each range compose anchors that measure the same quantity?
        families = module_coherence(module)
        coherent += sum(1 for f in families if f["status"] == "coherent")
        mixed += sum(1 for f in families if f["status"] == "mixed")
        # ADR-0008: does this shard's maximum say anything about being exceeded?
        for entry in module_exceedance(module):
            maxima_total += 1
            maxima_quantified += 1 if entry["quantified"] else 0
            maxima_none_known += 1 if entry["exceedance_basis"] == "none_known" else 0
        # ADR-0008 commitment 2: how much of the modeled loss comes from that maximum.
        # Analytic, so this costs no extra simulation.
        leverage = max_leverage(_scenario_impact(root, mid))
        if leverage is not None and leverage >= LEVERAGE_CONCERN:
            shards_tail_driven += 1
        # ADR-0016 part 3 amendment (2026-08-22): how much of each family's mean rests
        # on anchors measured on this shard's own cell. The page already carries the
        # corpus total and each parameter's own bridge flag; what it has never carried
        # is weight, and a count implies three anchors carry a third of the answer
        # each when one of them routinely carries over 90%. See finding 10.
        composed = compose_module(root, mid, provenance=module)
        cards = module.get("cards") or []
        cell_matched = sum(1 for c in cards
                           if (c.get("population") or {}).get("status") == "matched")
        shards.append({
            "id": mid,
            "leverage": leverage,
            "composition": composition_payload(composed),
            "params_cell_matched": cell_matched,
            "params_cross_cell": len(cards) - cell_matched,
            "coherence": [
                {"family": f["family"], "status": f["status"], "bases": f["bases"]}
                for f in families
            ],
            # The anchor-slot declaration: what statistical role each anchor really
            # plays versus the role its slot requires. Derived, never hand-written.
            "slots": [
                {"parameter": d["parameter"], "kind": d["kind"],
                 "central_tendency": d["central_tendency"],
                 "headline": d["headline"], "detail": d["detail"]}
                for d in slot_declarations(module)
            ],
            "title": module.get("title"),
            "country": ctx.get("country"),
            "industry": ctx.get("industry"),
            "size": ctx.get("company_size"),
            "threat": (mod or {}).get("threat"),
            "status": (mod or {}).get("status"),
            "avg": rng["avg"], "p95": rng["p95"], "p99": rng["p99"],
            "params": [{
                "parameter": c["parameter"], "value": c.get("value"), "unit": c.get("unit"),
                "status": c.get("status"), "confidence": c.get("confidence"),
                "source_name": c.get("source_name"), "source_type": c.get("source_type"),
                "publication_date": c.get("publication_date"), "quote": c.get("cited_line"),
                "caveat": c.get("caveat"),
                # ADR-0011: the population the source measured. Target-independent,
                # so it is what a reader computes their own distance from.
                "declared_for": c.get("declared_for"),
                # ADR-0003: whether the evidence is drawn from the shard's own cell,
                # and which dimension it is borrowed across when not. ADR-0011: a
                # computation against *this item's* cell, never a record property.
                "population": c.get("population"),
                # ADR-0007: what quantity this anchor measures, independent of who
                # it was measured on.
                "basis": c.get("measurement_basis"),
                # ADR-0008: what is known about this value being exceeded. Set on
                # impact maxima only — every other parameter carries null.
                "exceedance": c.get("exceedance_basis"),
                "exceedance_detail": c.get("exceedance_detail"),
            } for c in module["cards"]],
        })
    totals = dict(portfolio["totals"])
    totals["families_coherent"] = coherent
    totals["families_mixed"] = mixed
    totals["families_total"] = coherent + mixed
    # The anchor-slot declaration, as a cover fact beside coherence and exceedance.
    all_slots = [d for s in shards for d in s["slots"]]
    totals["slots_mode"] = sum(1 for d in all_slots if d["kind"] == "mode_slot")
    totals["slots_mode_central"] = sum(
        1 for s in shards
        for d in s["slots"] if d["kind"] == "mode_slot" and d["central_tendency"]
    )
    totals["slots_floor"] = sum(1 for d in all_slots if d["kind"] == "floor_slot")
    totals["maxima"] = maxima_total
    totals["maxima_quantified"] = maxima_quantified
    totals["maxima_none_known"] = maxima_none_known
    totals["shards_tail_driven"] = shards_tail_driven
    return {"totals": totals, "shards": shards, "repo": REPO_URL,
            "revisions": load_revisions(), "release": latest_release(),
            "aliases": load_aliases(), "site": SITE_URL}


def render(data, site_url=SITE_URL, asset_prefix=""):
    """Render the page.

    `asset_prefix` lets an archived per-release copy under docs/r/<release>/ reach the
    shared fonts at the site root instead of shipping its own duplicates.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":"))
    if "</script" in payload.lower():
        raise ValueError("data contains a closing script tag; refusing to inline")
    html = (template
            .replace("__RS_ASSETS__", asset_prefix)
            .replace("__RS_SITE__", site_url)
            .replace("__RS_DATA__", payload))
    for token in ("__RS_SITE__", "__RS_DATA__", "__RS_ASSETS__"):
        if token in html:
            raise ValueError(f"template placeholder {token} was left unfilled")
    return html


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the public risk-shard explorer page.")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "index.html")
    parser.add_argument(
        "--archive", action="store_true",
        help="Also write an immutable per-release copy under docs/r/<release>/ (ADR-0004). "
             "Existing archives are never regenerated.")
    args = parser.parse_args(argv)

    data = build_data(ROOT)
    html = render(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    t = data["totals"]
    print(f"Explorer written: {args.output}")
    print(f"  {t['shards']} shards · {t['params_source_backed']}/{t['params_total']} params source-backed")
    if data.get("release"):
        print(f"  citations pin to release {data['release']}")

    if args.archive:
        release = data.get("release")
        if not release:
            print("No data-pack release found — nothing to archive.")
            return 0
        archive = ROOT / "docs" / "r" / release / "index.html"
        if archive.exists():
            # A pinned citation must keep resolving to what it resolved to. Corrections
            # are a new release plus a revisions/ entry, never an edit in place.
            print(f"Archive already exists, left untouched: {archive}")
            return 0
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(render(data, asset_prefix="../../"), encoding="utf-8")
        print(f"Archived immutable copy: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
