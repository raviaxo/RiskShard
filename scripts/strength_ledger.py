#!/usr/bin/env python3
"""Strength-over-time progress ledger — record a release snapshot, or show the trend.

  record   Append the current source-strength snapshot to the ledger. No-op unless
           the data-pack fingerprint changed (i.e. a real release). Writes
           docs/internal/strength_ledger.json.
  show     Print the trend and the change since the prior release. Read-only.

The ledger is the canonical owner of the strength-over-time series; the weekly
Shard Notes digest reads its latest delta. Records nothing but the strength
metrics — it never touches scenarios or evidence.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.coherence import build_portfolio_coherence  # noqa: E402
from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.tail_sensitivity import build_tail_totals  # noqa: E402
from engine.readiness import build_readiness_dashboard  # noqa: E402
from engine.strength_ledger import (  # noqa: E402
    LEDGER_RELPATH,
    format_progress_markdown,
    latest_delta,
    record_snapshot,
    trend,
    update_readme_progress,
)


def _fmt_signed(n):
    return f"+{n}" if n > 0 else str(n)


def _format_metrics_line(metrics, delta):
    def cell(key):
        v = metrics.get(key, 0)
        if delta is None:
            return str(v)
        return f"{v} ({_fmt_signed(delta[key])})"

    def cell_if_measured(key):
        # Pre-split entries never measured the ADR-0003 keys; delta then omits
        # them too (compute_delta drops keys absent from either side).
        v = metrics.get(key, 0)
        if delta is None or key not in delta:
            return str(v)
        return f"{v} ({_fmt_signed(delta[key])})"

    lines = (
        f"  source-backed params : {cell('params_source_backed')} of {metrics.get('params_total', 0)}\n"
        f"  shards 6/6           : {cell('shards_fully_sourced')} of {metrics.get('shards', 0)}\n"
        f"  bridged / estimated  : {cell('params_bridged')}\n"
        f"  missing              : {cell('params_missing')}"
    )
    if "params_cell_matched" in metrics:
        lines += (
            f"\n  cell-matched         : {cell_if_measured('params_cell_matched')}"
            f" of {metrics.get('params_source_backed', 0)} source-backed\n"
            f"  population-bridged   : {cell_if_measured('params_cross_cell')}"
            f" ({cell_if_measured('params_cross_country')} cross-country)"
        )
    if "maxima_quantified" in metrics:
        lines += (
            f"\n  maxima w/ exceedance : {cell_if_measured('maxima_quantified')}"
            f" of {metrics['maxima']}\n"
            f"  maxima w/ none known : {cell_if_measured('maxima_none_known')}\n"
            f"  tail-driven shards   : {cell_if_measured('shards_tail_driven')}"
        )
    if "families_coherent" in metrics:
        families = metrics["families_coherent"] + metrics["families_mixed"]
        lines += (
            f"\n  coherent families    : {cell_if_measured('families_coherent')}"
            f" of {families}\n"
            f"  mixed families       : {cell_if_measured('families_mixed')}"
        )
    return lines


def _history(ledger_path):
    rows = trend(ledger_path)
    if not rows:
        print("Strength ledger is empty. Run `strength_ledger.py record` after a release.")
        return 0
    print("Strength trend (oldest first):")
    for entry, delta in rows:
        m = entry["metrics"]
        tag = "baseline" if delta is None else _fmt_signed(delta["params_source_backed"]) + " params"
        split = (
            f"cell-matched {m['params_cell_matched']}  " if "params_cell_matched" in m else ""
        )
        print(
            f"  {entry.get('date','?'):10}  {entry.get('data_pack_version','?'):12}  "
            f"source-backed {m['params_source_backed']}/{m['params_total']}  "
            f"{split}"
            f"6-of-6 {m['shards_fully_sourced']}/{m['shards']}  "
            f"bridged {m['params_bridged']}  [{tag}]"
        )
    return 0


def _show(ledger_path):
    latest, delta = latest_delta(ledger_path)
    if latest is None:
        print("Strength ledger is empty. Run `strength_ledger.py record` after a release.")
        return 0
    when = latest.get("date", "?")
    version = latest.get("data_pack_version", "?")
    print(f"Strength ledger — latest: {version} ({when})")
    if delta is None:
        print("  (baseline entry — no prior release to compare)")
    print(_format_metrics_line(latest["metrics"], delta))
    grades = latest.get("grades") or {}
    if grades:
        print("  grades               : " + ", ".join(f"{k}={v}" for k, v in sorted(grades.items())))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Strength-over-time progress ledger.")
    sub = parser.add_subparsers(dest="cmd")
    p_record = sub.add_parser(
        "record",
        help="Append a snapshot for a named release (no-op if the pack fingerprint is unchanged).",
    )
    p_record.add_argument(
        "--release",
        required=True,
        help="Release version this snapshot belongs to. Required: the ledger records "
             "releases, not every pack edit. Cutting a release with "
             "data_pack_manifest.py --release does this for you.",
    )
    p_record.add_argument(
        "--date",
        default=None,
        help="ISO date to stamp the entry (default: today).",
    )
    p_record.add_argument("--json", action="store_true")
    sub.add_parser("show", help="Print the latest release and the change since the prior one.")
    sub.add_parser("history", help="Print every recorded release, oldest first.")
    p_md = sub.add_parser("markdown", help="Emit the Progress table (Markdown) for the README.")
    p_md.add_argument(
        "--write-readme",
        action="store_true",
        help="Rewrite the table in README.md between the strength-ledger markers.",
    )
    args = parser.parse_args(argv)

    ledger_path = ROOT / LEDGER_RELPATH

    if args.cmd == "record":
        date = args.date or datetime.date.today().isoformat()
        dashboard = build_readiness_dashboard(ROOT)
        # ADR-0003: the split lives in the provenance layer, not the readiness matrix.
        population_totals = build_portfolio_provenance(ROOT)["totals"]
        # ADR-0007: construct lives in the coherence layer, measured by neither of
        # the other two. Folded in at the v0.5.0 cut, per the ADR-0003 precedent.
        coherence_totals = build_portfolio_coherence(ROOT)["totals"]
        # ADR-0008: the tail axis spans two modules; build_tail_totals merges them.
        tail_totals = build_tail_totals(ROOT)
        entry, appended, delta = record_snapshot(
            ledger_path,
            dashboard,
            date,
            args.release,
            population_totals=population_totals,
            coherence_totals=coherence_totals,
            tail_totals=tail_totals,
        )
        if args.json:
            print(json.dumps({"appended": appended, "entry": entry, "delta": delta}, indent=2, sort_keys=True))
            return 0
        if appended:
            print(f"Recorded {entry['data_pack_version']} ({entry['fingerprint'][:12]}) to the strength ledger.")
        else:
            print("No new release (fingerprint unchanged) — ledger not modified.")
        print(_format_metrics_line(entry["metrics"], delta))
        return 0

    if args.cmd == "history":
        return _history(ledger_path)

    if args.cmd == "markdown":
        if args.write_readme:
            changed = update_readme_progress(ROOT / "README.md", ledger_path)
            print("README.md progress table updated." if changed else "README.md already current.")
            return 0
        print(format_progress_markdown(ledger_path), end="")
        return 0

    # Default and `show`: read-only view.
    return _show(ledger_path)


if __name__ == "__main__":
    raise SystemExit(main())
