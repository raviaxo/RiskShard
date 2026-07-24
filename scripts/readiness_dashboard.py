#!/usr/bin/env python3
import argparse
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

from engine.readiness import build_readiness_dashboard, format_readiness_dashboard  # noqa: E402
from engine.strength_ledger import LEDGER_RELPATH, latest_delta  # noqa: E402


def _strength_trend_line(root):
    """One-line strength trend from the progress ledger, or '' if unavailable."""
    latest, delta = latest_delta(root / LEDGER_RELPATH)
    if latest is None:
        return ""
    m = latest["metrics"]
    head = (
        f"Strength trend: {m['params_source_backed']}/{m['params_total']} params "
        f"source-backed at {latest.get('data_pack_version', '?')}"
    )
    if delta is not None:
        d = delta["params_source_backed"]
        head += f" ({'+' if d > 0 else ''}{d} vs prior release)"
    else:
        head += " (baseline)"
    return head


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect global RiskShard readiness.")
    parser.add_argument(
        "--org-profile",
        default=ROOT / "org_profiles" / "au_finance_midmarket.yaml",
        type=Path,
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    dashboard = build_readiness_dashboard(ROOT, args.org_profile)
    if args.json:
        print(json.dumps(dashboard, indent=2, sort_keys=True))
    else:
        print(format_readiness_dashboard(dashboard), end="")
        trend_line = _strength_trend_line(ROOT)
        if trend_line:
            print(trend_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
