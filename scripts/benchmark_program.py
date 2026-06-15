#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.benchmark_program import (  # noqa: E402
    DEFAULT_TARGET_PATH,
    build_benchmark_program_report,
    format_benchmark_program_report,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect the RiskShard benchmark-grade 30 program.")
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGET_PATH)
    parser.add_argument("--target", help="Show one target by target id or module id.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = build_benchmark_program_report(ROOT, args.targets)
    if args.json:
        if args.target:
            report = {
                **report,
                "targets": [
                    target for target in report["targets"]
                    if target["id"] == args.target or target["module_id"] == args.target
                ],
            }
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_benchmark_program_report(report, target_id=args.target), end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
