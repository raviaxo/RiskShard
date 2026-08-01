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

from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.risk_modules import find_risk_module  # noqa: E402
from engine.web_console import WebConsoleApp  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "explorer_template.html"
REPO_URL = "https://github.com/raviaxo/RiskShard"
REVISIONS_DIR = ROOT / "revisions"
ALIASES_PATH = ROOT / "aliases.yaml"
RELEASES_DIR = ROOT / "data_pack_releases"
# Where the built page is served. Absolute URLs are required by Open Graph /
# Twitter cards, so link previews resolve when the page is shared.
SITE_URL = "https://raviaxo.github.io/RiskShard/"


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
    for module in portfolio["modules"]:
        mid = module["module_id"]
        mod = find_risk_module(mid, root)
        ctx = (mod or {}).get("context", {})
        rng = _loss_range(root, mid)
        shards.append({
            "id": mid,
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
                # ADR-0003: whether the evidence is drawn from the shard's own cell,
                # and which dimension it is borrowed across when not.
                "population": c.get("population"),
            } for c in module["cards"]],
        })
    return {"totals": portfolio["totals"], "shards": shards, "repo": REPO_URL,
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
