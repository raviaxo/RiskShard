#!/usr/bin/env python3
"""Report where module maturity labels drift from the benchmark gate (read-only).

Changes no labels.
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

from engine.maturity_audit import audit_maturity_labels, format_maturity_audit  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit module maturity labels vs. the benchmark gate.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = audit_maturity_labels(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_maturity_audit(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
