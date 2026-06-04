#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.data_packs import (  # noqa: E402
    build_data_pack_manifest,
    format_data_pack_manifest,
    write_data_pack_manifest,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate a RiskShard data-pack manifest.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
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
