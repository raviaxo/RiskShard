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

from engine.benchmark_program import (  # noqa: E402
    build_benchmark_cohort_report,
    build_benchmark_program_report,
    build_benchmark_sprint_report,
    format_benchmark_cohort_report,
    format_benchmark_program_report,
    format_benchmark_sprint_report,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect the RiskShard benchmark-grade 30 program.")
    parser.add_argument("--targets", type=Path, default=ROOT / "benchmark_targets" / "benchmark_grade_30.yaml")
    parser.add_argument("--target", help="Show one target by target id or module id.")
    parser.add_argument("--cohort", choices=["seeded"], help="Show a benchmark cohort summary.")
    parser.add_argument("--sprint", choices=["seeded"], help="Show a benchmark upgrade sprint.")
    parser.add_argument("--limit", type=int, help="Limit sprint target count.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = build_benchmark_program_report(ROOT, args.targets)
    if args.sprint:
        sprint_report = build_benchmark_sprint_report(report, args.sprint, limit=args.limit)
        if args.json:
            print(json.dumps(sprint_report, indent=2, sort_keys=True))
        else:
            print(format_benchmark_sprint_report(sprint_report), end="")
        return 0 if report["status"] == "pass" else 1

    if args.cohort:
        cohort_report = build_benchmark_cohort_report(report, args.cohort)
        if args.json:
            print(json.dumps(cohort_report, indent=2, sort_keys=True))
        else:
            print(format_benchmark_cohort_report(cohort_report), end="")
        return 0 if report["status"] == "pass" else 1

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
