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

from engine.beta_readiness import (  # noqa: E402
    build_beta_readiness_report,
    format_beta_readiness_report,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect RiskShard beta readiness.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the beta gate is not ready.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = build_beta_readiness_report(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_beta_readiness_report(report), end="")
    if args.strict and report["gate"]["status"] != "beta_ready":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
