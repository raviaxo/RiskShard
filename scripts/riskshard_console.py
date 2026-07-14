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

from engine.console import RiskShardConsole  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Start the interactive RiskShard console.")
    parser.add_argument(
        "--root",
        default=ROOT,
        type=Path,
        help="Repository root to use for scenarios, evidence, and results.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    console = RiskShardConsole(root=args.root)
    try:
        console.cmdloop()
    except KeyboardInterrupt:
        console.write("\nLeaving RiskShard console.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
