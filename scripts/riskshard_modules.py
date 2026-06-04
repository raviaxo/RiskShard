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
from engine.evidence_packs import (  # noqa: E402
    build_evidence_pack_registry,
    format_evidence_pack_detail,
    format_evidence_pack_registry,
)
from engine.risk_modules import (  # noqa: E402
    find_risk_module,
    format_module_detail,
    format_module_list,
    search_risk_modules,
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
    packs_parser.add_argument("--json", action="store_true")

    proposal_parser = subparsers.add_parser("propose", help="Propose evidence selectors for a module.")
    proposal_parser.add_argument("module_id")
    proposal_parser.add_argument("--org-profile", type=Path)
    proposal_parser.add_argument("--json", action="store_true")

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
