#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.contributor import (  # noqa: E402
    build_contributor_preflight,
    format_contributor_preflight,
    format_scaffold_result,
    scaffold_contributor_pack,
)


def parse_args(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "scaffold":
        parser = argparse.ArgumentParser(description="Create a starter RiskShard contributor pack.")
        parser.add_argument("command")
        parser.add_argument("pack_path", help="Directory where the starter pack should be written.")
        parser.add_argument("--module-id", required=True)
        parser.add_argument("--country", required=True)
        parser.add_argument("--industry", required=True)
        parser.add_argument("--company-size", required=True)
        parser.add_argument("--threat", required=True)
        parser.add_argument("--title")
        parser.add_argument("--currency", default="USD")
        parser.add_argument("--status", default="governed_starter")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--json", action="store_true")
        return parser.parse_args(argv)

    parser = argparse.ArgumentParser(description="Run contributor preflight checks.")
    parser.add_argument(
        "pack_path",
        nargs="?",
        help="Optional proposed content pack directory to validate before a pull request.",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if getattr(args, "command", None) == "scaffold":
        try:
            result = scaffold_contributor_pack(
                ROOT,
                args.pack_path,
                module_id=args.module_id,
                country=args.country,
                industry=args.industry,
                company_size=args.company_size,
                threat=args.threat,
                title=args.title,
                currency=args.currency,
                status=args.status,
                force=args.force,
            )
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(format_scaffold_result(result), end="")
        return 0

    preflight = build_contributor_preflight(ROOT, pack_path=args.pack_path)
    if args.json:
        print(json.dumps(preflight, indent=2, sort_keys=True))
    else:
        print(format_contributor_preflight(preflight), end="")
    return 0 if preflight["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
