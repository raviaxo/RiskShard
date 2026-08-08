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
from engine.coverage import (  # noqa: E402
    build_coverage_report,
    format_coverage_report,
)
from engine.exceedance import (  # noqa: E402
    build_portfolio_exceedance,
    format_portfolio_markdown as format_exceedance_markdown,
)
from engine.coherence import (  # noqa: E402
    build_portfolio_coherence,
    format_portfolio_markdown as format_coherence_markdown,
)
from engine.provenance import (  # noqa: E402
    build_dispute_issue,
    build_module_provenance,
    build_portfolio_provenance,
    dispute_issue_url,
    format_portfolio_markdown,
    format_provenance,
    repo_slug_from_remote,
)
from engine.interop import format_pyfair_code, to_pyfair  # noqa: E402
from engine.scenarios import load_scenario  # noqa: E402
from engine.scaffold import next_steps, scaffold_shard  # noqa: E402


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

    coverage_parser = subparsers.add_parser("coverage", help="Grade shard data strength and confidence.")
    coverage_parser.add_argument("module_id", nargs="?")
    coverage_parser.add_argument("--json", action="store_true")

    coherence_parser = subparsers.add_parser(
        "coherence",
        help="Do a range's min/likely/max anchors measure the same quantity? (ADR-0007)",
    )
    coherence_parser.add_argument("module_id", nargs="?")
    coherence_parser.add_argument(
        "--report",
        type=Path,
        metavar="PATH",
        help="Write the Markdown coherence report to PATH.",
    )
    coherence_parser.add_argument("--json", action="store_true")

    exceedance_parser = subparsers.add_parser(
        "exceedance",
        help="Does a shard's impact.max say anything about being exceeded? (ADR-0008)",
    )
    exceedance_parser.add_argument("module_id", nargs="?")
    exceedance_parser.add_argument(
        "--report",
        type=Path,
        metavar="PATH",
        help="Write the Markdown exceedance report to PATH.",
    )
    exceedance_parser.add_argument("--json", action="store_true")

    prov_parser = subparsers.add_parser(
        "provenance", help="Challenge a number: show value, source, quote, and caveat per parameter."
    )
    prov_parser.add_argument("module_id", nargs="?")
    prov_parser.add_argument("parameter", nargs="?", help="Limit to one parameter, e.g. frequency.max.")
    prov_parser.add_argument(
        "--dispute",
        metavar="PARAMETER",
        help="Print a pre-filled 'dispute this evidence' GitHub issue URL for the parameter.",
    )
    prov_parser.add_argument(
        "--all",
        action="store_true",
        help="Whole-portfolio evidence report: every number, source, and caveat.",
    )
    prov_parser.add_argument(
        "--report",
        type=Path,
        metavar="PATH",
        help="With --all, write the Markdown evidence report to PATH.",
    )
    prov_parser.add_argument("--json", action="store_true")

    export_parser = subparsers.add_parser(
        "export", help="Export a shard to another engine's format (spike: pyfair)."
    )
    export_parser.add_argument("module_id")
    export_parser.add_argument("--format", default="pyfair", choices=["pyfair"])
    export_parser.add_argument("--json", action="store_true")

    new_parser = subparsers.add_parser(
        "new-shard", help="Scaffold a new shard skeleton (all 6 files, placeholder estimates)."
    )
    new_parser.add_argument("--country", required=True, help="ISO code, e.g. NO, BR, IN.")
    new_parser.add_argument("--industry", required=True, help="e.g. financial_services, manufacturing.")
    new_parser.add_argument("--threat", required=True, help="e.g. ransomware, data_breach, business_email_compromise.")
    new_parser.add_argument("--size", default="mid_market", help="Company size band (default mid_market).")
    new_parser.add_argument("--dry-run", action="store_true", help="Show the files that would be created.")
    new_parser.add_argument("--overwrite", action="store_true", help="Replace an existing shard of the same id.")
    new_parser.add_argument("--json", action="store_true")

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

    if command == "coverage":
        report = build_coverage_report(ROOT, module_id=args.module_id)
        if args.module_id and not report["shards"]:
            print(f"Unknown risk module: {args.module_id}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(format_coverage_report(report), end="")
        return 0

    if command == "coherence":
        module_ids = [args.module_id] if args.module_id else None
        portfolio = build_portfolio_coherence(ROOT, module_ids=module_ids)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(format_coherence_markdown(portfolio), encoding="utf-8")
            print(f"Coherence report written: {args.report}")
        elif args.json:
            print(json.dumps(portfolio, indent=2, sort_keys=True))
        else:
            print(format_coherence_markdown(portfolio), end="")
        return 0

    if command == "exceedance":
        module_ids = [args.module_id] if args.module_id else None
        portfolio = build_portfolio_exceedance(ROOT, module_ids=module_ids)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(format_exceedance_markdown(portfolio), encoding="utf-8")
            print(f"Exceedance report written: {args.report}")
        elif args.json:
            print(json.dumps(portfolio, indent=2, sort_keys=True))
        else:
            print(format_exceedance_markdown(portfolio), end="")
        return 0

    if command == "provenance":
        if args.all:
            portfolio = build_portfolio_provenance(ROOT)
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(format_portfolio_markdown(portfolio), encoding="utf-8")
                print(f"Evidence report written: {args.report}")
            elif args.json:
                print(json.dumps(portfolio, indent=2, sort_keys=True))
            else:
                print(format_portfolio_markdown(portfolio), end="")
            return 0

        if not args.module_id:
            print("provenance requires a module_id (or --all)", file=sys.stderr)
            return 1
        module = find_risk_module(args.module_id, ROOT)
        if module is None:
            print(f"Unknown risk module: {args.module_id}", file=sys.stderr)
            return 1
        provenance = build_module_provenance(args.module_id, ROOT)

        if args.dispute:
            try:
                issue = build_dispute_issue(provenance, args.dispute)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            url = dispute_issue_url(_repo_slug(), issue)
            if args.json:
                print(json.dumps({"issue": issue, "url": url}, indent=2, sort_keys=True))
            else:
                print(f"Dispute {args.module_id} / {args.dispute}:\n")
                print(issue["body"])
                print(f"\nOpen the pre-filled issue:\n{url}")
            return 0

        if args.json:
            print(json.dumps(provenance, indent=2, sort_keys=True))
        else:
            print(format_provenance(provenance, parameter=args.parameter), end="")
        return 0

    if command == "export":
        scenario_path = ROOT / "scenarios" / f"{args.module_id}.yaml"
        if not scenario_path.exists():
            print(f"No scenario file for shard: {args.module_id}", file=sys.stderr)
            return 1
        scenario = load_scenario(scenario_path)
        try:
            if args.json:
                print(json.dumps(to_pyfair(scenario), indent=2, sort_keys=True))
            else:
                print(format_pyfair_code(scenario, module_id=args.module_id), end="")
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if command == "new-shard":
        try:
            result = scaffold_shard(
                ROOT, args.country, args.industry, args.size, args.threat,
                dry_run=args.dry_run, overwrite=args.overwrite,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({**result, "next_steps": next_steps(result["shard_id"])}, indent=2, sort_keys=True))
            return 0
        verb = "Would create" if result["dry_run"] else "Created"
        print(f"{verb} shard {result['shard_id']} ({len(result['written'])} files):")
        for rel in result["written"]:
            print(f"  {rel}")
        print("\nNext steps:")
        for step in next_steps(result["shard_id"]):
            print(f"  {step}")
        return 0

    return 0


def _repo_slug():
    """Repo owner/name from git origin, for dispute URLs; falls back gracefully."""
    import subprocess

    try:
        url = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return repo_slug_from_remote(url) or ""
    except Exception:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
