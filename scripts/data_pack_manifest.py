#!/usr/bin/env python3
import argparse
import datetime
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

from engine.data_packs import (  # noqa: E402
    build_data_pack_manifest,
    build_data_pack_release,
    format_data_pack_manifest,
    format_data_pack_release,
    write_data_pack_manifest,
    write_data_pack_release,
)
from engine.coherence import build_portfolio_coherence  # noqa: E402
from engine.tail_sensitivity import build_tail_totals  # noqa: E402
from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.readiness import build_readiness_dashboard  # noqa: E402
from engine.strength_ledger import (  # noqa: E402
    LEDGER_RELPATH,
    build_axis_totals,
    record_snapshot,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate a RiskShard data-pack manifest.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--release", help="Write a named data-pack release artifact with this version.")
    parser.add_argument(
        "--release-dir",
        default=ROOT / "data_pack_releases",
        type=Path,
        help="Directory for named data-pack release artifacts.",
    )
    parser.add_argument("--notes", help="Optional release notes stored in the release artifact.")
    parser.add_argument(
        "--no-ledger",
        action="store_true",
        help="Skip appending a strength-ledger entry when cutting a release.",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.release:
        release = build_data_pack_release(ROOT, version=args.release, notes=args.notes)
        path = write_data_pack_release(release, args.release_dir)
        ledger_msg = None
        if not args.no_ledger:
            # Cutting a release is exactly when the strength trend should tick.
            # record_snapshot is a no-op if this pack's fingerprint is already logged.
            dashboard = build_readiness_dashboard(ROOT)
            # Every declared axis, built in one place so a new one cannot reach this
            # call site and miss the other (it did, at this cut).
            entry, appended, _ = record_snapshot(
                ROOT / LEDGER_RELPATH,
                dashboard,
                datetime.date.today().isoformat(),
                args.release,
                **build_axis_totals(ROOT),
            )
            ledger_msg = (
                f"Strength ledger: recorded {entry['data_pack_version']}."
                if appended
                else "Strength ledger: fingerprint already logged (no change)."
            )
        if args.json:
            print(json.dumps(release, indent=2, sort_keys=True))
        else:
            print(f"Data-pack release saved: {path}")
            print(format_data_pack_release(release), end="")
            if ledger_msg:
                print(ledger_msg)
        return 0

    manifest = build_data_pack_manifest(ROOT)
    if args.output:
        path = write_data_pack_manifest(manifest, args.output)
        print(f"Data-pack manifest saved: {path}")
    elif args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(format_data_pack_manifest(manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
