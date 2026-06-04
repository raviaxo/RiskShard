#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.contributor import build_contributor_preflight, format_contributor_preflight  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run contributor preflight checks.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    preflight = build_contributor_preflight(ROOT)
    if args.json:
        print(json.dumps(preflight, indent=2, sort_keys=True))
    else:
        print(format_contributor_preflight(preflight), end="")
    return 0 if preflight["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
