#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.governance import build_data_feed_inventory, format_data_feed_inventory  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect RiskShard data feed governance.")
    parser.add_argument("--registry", default=ROOT / "sources" / "registry.yaml", type=Path)
    parser.add_argument("--manifest", default=ROOT / "sources" / "manifest.json", type=Path)
    parser.add_argument("--evidence", default=ROOT / "evidence", type=Path)
    parser.add_argument("--json", action="store_true", help="Write machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    inventory = build_data_feed_inventory(
        registry_path=args.registry,
        manifest_path=args.manifest,
        evidence_path=args.evidence,
    )
    if args.json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(format_data_feed_inventory(inventory), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
