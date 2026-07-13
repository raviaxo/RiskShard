#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.calibration_assistant import (  # noqa: E402
    format_module_calibration_proposal,
    propose_module_calibration,
)
from engine.country_priorities import (  # noqa: E402
    find_country_priority,
    format_country_priorities,
    format_country_priority_detail,
    top_country_priorities,
)
from engine.evidence_packs import (  # noqa: E402
    build_evidence_pack_artifact,
    build_evidence_pack_registry,
    format_evidence_pack_artifact,
    format_evidence_pack_detail,
    format_evidence_pack_registry,
    write_evidence_pack_artifact,
)
from engine.risk_modules import (  # noqa: E402
    find_risk_module,
    format_module_detail,
    format_module_list,
    search_risk_modules,
)
from engine.shard_registry import (  # noqa: E402
    build_shard_registry,
    format_shard_registry,
    write_shard_registry,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect RiskShard risk modules and evidence packs.")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List or search risk modules.")
    list_parser.add_argument("query", nargs="*", help="Optional search terms.")
    list_parser.add_argument("--json", action="store_true")

    info_parser = subparsers.add_parser("info", help="Inspect one risk module.")
    info_parser.add_argument("module_id")
    info_parser.add_argument("--json", action="store_true")

    packs_parser = subparsers.add_parser("packs", help="Inspect governed evidence packs.")
    packs_parser.add_argument("module_id", nargs="?")
    packs_parser.add_argument("--export", type=Path, help="Write one module evidence-pack artifact JSON.")
    packs_parser.add_argument("--json", action="store_true")

    proposal_parser = subparsers.add_parser("propose", help="Propose evidence selectors for a module.")
    proposal_parser.add_argument("module_id")
    proposal_parser.add_argument("--org-profile", type=Path)
    proposal_parser.add_argument("--json", action="store_true")

    countries_parser = subparsers.add_parser("countries", help="Show prioritized country expansion targets.")
    countries_parser.add_argument("country_id", nargs="?")
    countries_parser.add_argument("--limit", default=25, type=int)
    countries_parser.add_argument("--json", action="store_true")

    registry_parser = subparsers.add_parser("registry", help="Export the machine-readable shard registry.")
    registry_parser.add_argument("--output", type=Path, help="Write registry JSON to this path.")
    registry_parser.add_argument("--json", action="store_true")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    command = args.command or "list"

    if command == "list":
        modules = search_risk_modules(" ".join(args.query), ROOT)
        if args.json:
            print(json.dumps(modules, indent=2, sort_keys=True))
        else:
            print(format_module_list(modules), end="")
        return 0

    if command == "info":
        module = find_risk_module(args.module_id, ROOT)
        if module is None:
            print(f"Unknown risk module: {args.module_id}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(module, indent=2, sort_keys=True))
        else:
            print(format_module_detail(module), end="")
        return 0

    if command == "packs":
        if args.export:
            if not args.module_id:
                print("--export requires a module_id", file=sys.stderr)
                return 1
            try:
                artifact = build_evidence_pack_artifact(args.module_id, ROOT)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            path = write_evidence_pack_artifact(artifact, args.export)
            if args.json:
                print(json.dumps(artifact, indent=2, sort_keys=True))
            else:
                print(f"Evidence pack artifact saved: {path}")
                print(format_evidence_pack_artifact(artifact), end="")
            return 0

        registry = build_evidence_pack_registry(ROOT, module_id=args.module_id)
        if args.json:
            print(json.dumps(registry, indent=2, sort_keys=True))
        elif args.module_id:
            if not registry["packs"]:
                print(f"Unknown evidence pack module: {args.module_id}", file=sys.stderr)
                return 1
            print(format_evidence_pack_detail(registry["packs"][0]), end="")
        else:
            print(format_evidence_pack_registry(registry), end="")
        return 0

    if command == "propose":
        try:
            proposal = propose_module_calibration(
                args.module_id,
                root=ROOT,
                org_profile_path=args.org_profile,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(proposal, indent=2, sort_keys=True))
        else:
            print(format_module_calibration_proposal(proposal), end="")
        return 0

    if command == "countries":
        if args.country_id:
            item = find_country_priority(args.country_id)
            if item is None:
                print(f"Unknown country priority: {args.country_id}", file=sys.stderr)
                return 1
            if args.json:
                print(json.dumps(item, indent=2, sort_keys=True))
            else:
                print(format_country_priority_detail(item), end="")
            return 0

        priorities = top_country_priorities(args.limit)
        if args.json:
            print(json.dumps(priorities, indent=2, sort_keys=True))
        else:
            print(format_country_priorities(priorities), end="")
        return 0

    if command == "registry":
        registry = build_shard_registry(ROOT)
        if args.output:
            path = write_shard_registry(registry, args.output)
            if not args.json:
                print(f"Shard registry saved: {path}")
                print(format_shard_registry(registry), end="")
                return 0
        if args.json or args.output:
            print(json.dumps(registry, indent=2, sort_keys=True))
        else:
            print(format_shard_registry(registry), end="")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
