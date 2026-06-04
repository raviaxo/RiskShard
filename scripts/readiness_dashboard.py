#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.readiness import build_readiness_dashboard, format_readiness_dashboard  # noqa: E402


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
