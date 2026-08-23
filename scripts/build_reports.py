#!/usr/bin/env python3
"""Publish the executive report for every shard as a page.

The report has existed since v0.3.0 and, until now, only inside the console: a
person had to clone the repository and start an interactive session to see one.
It is also the most directly usable thing this project produces — a one-page
board-facing summary that, since v0.11.0, states *who the evidence was measured
on* and not merely that it is published.

**This publishes an artifact that is already generated; it does not invent one.**
The content comes from `engine.executive_report`, which has a single Markdown
source rendered two ways, so a published page and a console-generated `.md`
cannot disagree. [ADR-0016](../docs/adr/0016-the-audit-is-the-product.md) part 1
asks whether a proposal adds a row to a finite table or a parameter to an
infinite one: this is eleven rows, one per published shard, and it stops growing
when the shards do.

    python scripts/build_reports.py            # write docs/reports/
    python scripts/build_reports.py --check    # render only; fail on an unfilled token
"""
import argparse
import html
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.evidence_packs import build_evidence_pack_registry  # noqa: E402
from engine.executive_report import (build_executive_report,  # noqa: E402
                                     format_executive_report_html)
from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.web_console import WebConsoleApp  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "report_template.html"
INDEX_TEMPLATE = Path(__file__).resolve().parent / "report_index_template.html"
SITE_URL = "https://raviaxo.github.io/RiskShard/"


def build_report(app, module_id):
    """One shard's report, through exactly the path the console uses."""
    app.run_command(f"use {module_id}")
    app.run_command("run")
    console = app.console
    module = console.current_module()
    registry = build_evidence_pack_registry(ROOT, module_id=module["id"])
    pack = registry["packs"][0] if registry["packs"] else {}
    return build_executive_report(console.last_run, module, pack, root=ROOT)


def render(report, release, site_url=SITE_URL):
    context = report.get("context") or {}
    label = " · ".join(str(v).replace("_", " ") for v in (
        context.get("country"), context.get("industry"), context.get("company_size"),
        report.get("threat")) if v)
    description = (
        f"Executive summary for {label}. Modeled annual loss with what the figure rests on, "
        "stated per family: how much of it was measured on this exact context and how much "
        "was measured somewhere else."
    )
    nav = (
        f'<a href="{site_url}#{report["module_id"]}">See the evidence behind this figure</a> · '
        f'<a href="{site_url}audit.html">What the sources actually publish</a> · '
        f'<a href="index.html">All summaries</a>'
    )
    fields = {
        "__RS_TITLE__": html.escape(f"{report['title']} — RiskShard executive summary"),
        "__RS_DESC__": html.escape(description),
        "__RS_BODY__": format_executive_report_html(report),
        "__RS_SHARD__": html.escape(report["module_id"] or ""),
        "__RS_RELEASE__": html.escape(release or "unreleased"),
        "__RS_NAV__": nav,
        "__RS_SITE__": site_url,
    }
    markup = TEMPLATE.read_text(encoding="utf-8")
    for token, value in fields.items():
        markup = markup.replace(token, value)
    return markup


def render_index(reports, release, site_url=SITE_URL):
    rows = []
    for report in reports:
        context = report.get("context") or {}
        cell = " · ".join(str(v).replace("_", " ") for v in (
            context.get("country"), context.get("industry"), context.get("company_size"),
            report.get("threat")) if v)
        composed = (report.get("composition") or {}).get("families") or {}
        if {"frequency", "impact"} <= set(composed):
            measured = " / ".join(
                f"{round(composed[f]['measured_share'] * 100)}%" for f in ("frequency", "impact"))
        else:
            measured = "—"
        amount = f"{report['currency'] or ''} {round(report['mean']):,}".strip()
        rows.append(
            f'<tr><td><a href="{html.escape(report["module_id"])}.html">'
            f'{html.escape(cell or report["module_id"])}</a></td>'
            f'<td style="text-align:right">{html.escape(amount)}</td>'
            f'<td style="text-align:right">{measured}</td></tr>'
        )
    fields = {
        "__RS_ROWS__": "".join(rows),
        "__RS_COUNT__": str(len(reports)),
        "__RS_RELEASE__": html.escape(release or "unreleased"),
        "__RS_SITE__": site_url,
    }
    markup = INDEX_TEMPLATE.read_text(encoding="utf-8")
    for token, value in fields.items():
        markup = markup.replace(token, value)
    return markup


def latest_release():
    directory = ROOT / "data_pack_releases"
    versions = sorted(p.stem for p in directory.glob("*.json")) if directory.exists() else []
    return versions[-1] if versions else ""


def main(argv=None):
    parser = argparse.ArgumentParser(description="Publish the per-shard executive summaries.")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "reports")
    parser.add_argument("--check", action="store_true",
                        help="render without writing; exit non-zero if a token is left unfilled")
    args = parser.parse_args(argv)

    release = latest_release()
    app = WebConsoleApp(root=ROOT)
    module_ids = [m["module_id"] for m in build_portfolio_provenance(ROOT)["modules"]]
    reports = [build_report(app, module_id) for module_id in module_ids]
    pages = {report["module_id"]: render(report, release) for report in reports}
    pages["index"] = render_index(reports, release)

    unfilled = [name for name, markup in pages.items() if "__RS_" in markup]
    if unfilled:
        print(f"Unfilled template token remains in: {', '.join(sorted(unfilled))}")
        return 1
    if args.check:
        print(f"Executive summaries render clean ({len(reports)} shards).")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    for name, markup in pages.items():
        (args.output / f"{name}.html").write_text(markup, encoding="utf-8")
    print(f"Executive summaries written: {args.output} ({len(reports)} shards, pinned {release})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
