#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.evidence_quality import has_errors, validate_evidence_quality  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Validate RiskShard evidence quality gates.")
    parser.add_argument("--evidence", default=ROOT / "evidence", type=Path)
    parser.add_argument("--manifest", default=ROOT / "sources" / "manifest.json", type=Path)
    return parser.parse_args()


def main(argv=None):
    args = parse_args()
    issues = validate_evidence_quality(args.evidence, args.manifest)

    if not issues:
        print("Evidence quality gates passed with no issues.")
        return 0

    for item in issues:
        print(f"{item['severity'].upper()} {item['code']} {item['record_id']}: {item['message']}")

    return 1 if has_errors(issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
