#!/usr/bin/env python3
"""Probe whether a guard fails when the thing it checks is wrong.

Restores every file it touches, including when a test run raises. Changes nothing
permanently.

    python scripts/mutation_probe.py \
        tests.test_published_claims.PublishedClaims.test_the_readme_carries_the_date_the_count_was_read \
        --mutate README.md "2026-08-16" "2026-11-12" --occurrence 1
"""
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

from engine.mutation import HAS_TEETH, format_probe, probe  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Mutate what a guard checks and confirm the guard fails.",
    )
    parser.add_argument("test", help="unittest selector, e.g. tests.test_x.Case.test_y")
    parser.add_argument(
        "--mutate", nargs=3, action="append", metavar=("PATH", "OLD", "NEW"),
        required=True, help="repeatable; each mutation is applied on its own",
    )
    parser.add_argument(
        "--occurrence", type=int, action="append", default=None,
        help="1-based occurrence for the matching --mutate; repeat to pair positionally",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    occurrences = args.occurrence or []
    mutations = []
    for i, (path, old, new) in enumerate(args.mutate):
        spec = {"path": path, "old": old, "new": new}
        if i < len(occurrences):
            spec["occurrence"] = occurrences[i]
        mutations.append(spec)

    report = probe(ROOT, args.test, mutations)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_probe(report), end="")
    return 0 if report["verdict"] == HAS_TEETH else 1


if __name__ == "__main__":
    raise SystemExit(main())
