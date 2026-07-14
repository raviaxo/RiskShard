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

from engine.experience import format_top_risks, rank_top_risks  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rank starter threats by calibration readiness.")
    parser.add_argument(
        "--org-profile",
        type=Path,
        default=ROOT / "org_profiles" / "au_finance_midmarket.yaml",
        help="Organization profile to match against evidence.",
    )
    parser.add_argument("--evidence", type=Path, default=ROOT / "evidence")
    parser.add_argument("--manifest", type=Path, default=ROOT / "sources" / "manifest.json")
    parser.add_argument(
        "--threat-library",
        type=Path,
        default=ROOT / "threat_library" / "starter_pack.yaml",
    )
    parser.add_argument("--calibration-dir", type=Path, default=ROOT / "calibrations")
    parser.add_argument("--limit", type=int, help="Limit the number of ranked threats.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    rows = rank_top_risks(
        args.org_profile,
        evidence_path=args.evidence,
        manifest_path=args.manifest,
        threat_library_path=args.threat_library,
        calibration_dir=args.calibration_dir,
    )
    if args.limit is not None:
        rows = rows[:args.limit]

    if args.json:
        print(json.dumps({
            "org_profile": str(args.org_profile),
            "risk_count": len(rows),
            "risks": rows,
        }, indent=2, sort_keys=True))
    else:
        print(format_top_risks(rows), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
