#!/usr/bin/env python3
"""Audit source_type values against the canonical vocabulary (read-only).

Reports any source_type that is not a vetted base type and does not follow a
bridge/derived/assumption convention. Changes nothing.
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

from engine.source_type_audit import audit_source_types, format_source_type_audit  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit source_type values against the canonical vocabulary.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = audit_source_types(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_source_type_audit(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
