#!/usr/bin/env python3
"""Print a "Shard Notes" weekly digest skeleton (read-only).

Auto-fills state, shipped, and contributors from the repo; leaves Lesson and Next
for you. Changes nothing.
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

from engine.weekly_digest import build_weekly_digest, format_weekly_digest  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print a Shard Notes weekly digest skeleton.")
    parser.add_argument("--days", type=int, default=7, help="Look back this many days for activity.")
    parser.add_argument("--week-of", default=None, help="Label for the week, e.g. 'Jul 21'.")
    parser.add_argument("--owner", default=None, help="Your name, to exclude from the 'from the community' line.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    digest = build_weekly_digest(ROOT, since_days=args.days)
    if args.json:
        print(json.dumps(digest, indent=2, sort_keys=True))
    else:
        print(format_weekly_digest(digest, week_of=args.week_of, owner_name=args.owner), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
