from pathlib import Path

from engine.benchmark_program import build_benchmark_program_report
from engine.clean_install import load_clean_install_proof, summarize_clean_install_proof
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.package_smoke import build_package_smoke_report
from engine.readiness import build_readiness_dashboard


PROJECT_ROOT = Path(__file__).resolve().parent.parent

BETA_TARGETS = {
    "benchmark_targets": 30,
    "governed_modules": 10,
    "benchmark_ready_candidates": 3,
}

CORE_CONSOLE_COMMANDS = {
    "riskshard-console",
    "riskshard-web-console",
    "riskshard-beta",
}

MINIMUM_GOVERNANCE_DOCS = {
    "docs/METHODOLOGY.md",
    "CONTRIBUTING.md",
    "docs/BENCHMARK_CONTRIBUTOR_WORKFLOW.md",
    "docs/CONSOLE_EXPERIENCE.md",
}

DEFERRED_OPERATING_MODEL = [
    "full issue and pull request template suite",
    "public contributor campaign",
    "marketing launch page or broad announcement",
    "formal maintainer role matrix",
    "community label taxonomy beyond what active maintainers need",
]


def build_beta_readiness_report(root=PROJECT_ROOT):
    root = Path(root)
    benchmark = build_benchmark_program_report(root)
    dashboard = build_readiness_dashboard(root)
    package = build_package_smoke_report(root)
    evidence_issues = validate_evidence_quality(
        root / "evidence",
        root / "sources" / "manifest.json",
    )
    evidence_errors = [issue for issue in evidence_issues if issue["severity"] == "error"]
    package_entry_points = {item["name"]: item for item in package["entry_points"]}
    clean_install = summarize_clean_install_proof(load_clean_install_proof(root / "release" / "clean_install_proof.json"))

    checks = [
        at_least_check(
            "BETA-DATA-01",
            "Benchmark target map",
            "data depth",
            benchmark["target_count"],
            BETA_TARGETS["benchmark_targets"],
            "Thirty benchmark targets are defined before beta planning broadens.",
            "python scripts/benchmark_program.py",
        ),
        at_least_check(
            "BETA-DATA-02",
            "Runnable governed modules",
            "data depth",
            benchmark["module_seeded_count"],
            BETA_TARGETS["governed_modules"],
            "Beta should have enough modules to feel like a library, not only a demo.",
            "python scripts/riskshard_modules.py list",
        ),
        at_least_check(
            "BETA-DATA-03",
            "Benchmark-ready candidates",
            "data depth",
            benchmark["benchmark_ready_count"],
            BETA_TARGETS["benchmark_ready_candidates"],
            "At least three modules should clear the automated benchmark gate before public benchmark claims.",
            "python scripts/benchmark_program.py --cohort seeded",
        ),
        boolean_check(
            "BETA-GOV-01",
            "Source feed health",
            "governance",
            not dashboard["feed_governance"]["problem_feeds"],
            f"{dashboard['feed_governance']['feed_count'] - len(dashboard['feed_governance']['problem_feeds'])}/{dashboard['feed_governance']['feed_count']} feeds current",
            "All active governed source feeds should be current.",
            "python scripts/data_governance.py",
        ),
        boolean_check(
            "BETA-GOV-02",
            "Evidence quality gates",
            "governance",
            not has_errors(evidence_issues),
            f"{len(evidence_errors)} errors",
            "Evidence quality should have no blocking errors.",
            "python scripts/validate_evidence.py",
        ),
        boolean_check(
            "BETA-ENG-01",
            "Package entry-point smoke",
            "engineering",
            package["status"] == "pass",
            package["status"],
            "Declared local console entry points should be importable callables.",
            "python scripts/package_smoke.py",
        ),
        boolean_check(
            "BETA-ENG-02",
            "Core console commands packaged",
            "engineering",
            all(
                package_entry_points.get(name, {}).get("status") == "pass"
                for name in CORE_CONSOLE_COMMANDS
            ),
            ", ".join(sorted(CORE_CONSOLE_COMMANDS)),
            "The practitioner console, browser console, and beta gate should be packaged.",
            "python scripts/package_smoke.py",
        ),
        boolean_check(
            "BETA-ENG-03",
            "Clean install proof",
            "engineering",
            clean_install["status"] == "pass",
            clean_install["detail"],
            "Before beta, verify installation and entry points in a fresh virtual environment or CI job.",
            "python scripts/clean_install_proof.py --recreate",
        ),
        boolean_check(
            "BETA-REL-01",
            "Data-pack fingerprint",
            "release discipline",
            len(dashboard["data_pack"]["fingerprint"]) == 64,
            dashboard["data_pack"]["fingerprint"][:12],
            "Beta demos and reviews should pin to a governed data-pack fingerprint.",
            "python scripts/data_pack_manifest.py",
        ),
        boolean_check(
            "BETA-DOC-01",
            "Minimum governance docs",
            "documentation",
            all((root / path).exists() for path in MINIMUM_GOVERNANCE_DOCS),
            f"{sum(1 for path in MINIMUM_GOVERNANCE_DOCS if (root / path).exists())}/{len(MINIMUM_GOVERNANCE_DOCS)} docs",
            "Keep only the docs needed to build and vet the product before scaling public operations.",
            "python scripts/beta_readiness.py",
        ),
        boolean_check(
            "BETA-DOC-02",
            "Contributor preflight available",
            "documentation",
            package_entry_points.get("riskshard-preflight", {}).get("status") == "pass",
            package_entry_points.get("riskshard-preflight", {}).get("status", "missing"),
            "Minimal contribution guardrails should exist even before a full public operating model.",
            "python scripts/contributor_preflight.py",
        ),
    ]

    blocking_checks = [check for check in checks if check["blocks_beta"]]
    passed = [check for check in blocking_checks if check["status"] == "pass"]
    failed = [check for check in blocking_checks if check["status"] == "fail"]
    gate = {
        "status": "beta_ready" if not failed else "not_beta_ready",
        "passed": len(passed),
        "total": len(blocking_checks),
        "failed": len(failed),
        "summary": beta_summary(passed, blocking_checks, failed),
    }

    return {
        "gate": gate,
        "targets": BETA_TARGETS,
        "checks": checks,
        "next_beta_moves": next_beta_moves(failed, benchmark),
        "deferred_operating_model": DEFERRED_OPERATING_MODEL,
        "supporting_reports": {
            "benchmark_status_counts": benchmark["status_counts"],
            "risk_module_count": dashboard["risk_modules"]["module_count"],
            "feed_status_counts": dashboard["feed_governance"]["status_counts"],
            "package_status": package["status"],
        },
    }


def beta_summary(passed, blocking_checks, failed):
    ratio = f"{len(passed)}/{len(blocking_checks)} beta checks pass"
    if not failed:
        return f"{ratio}; RiskShard is ready for beta review."
    return f"{ratio}; keep building product and data depth before scaling public operations."


def at_least_check(requirement_id, name, area, actual, target, rationale, command):
    status = "pass" if actual >= target else "fail"
    return {
        "id": requirement_id,
        "name": name,
        "area": area,
        "status": status,
        "actual": actual,
        "target": target,
        "detail": f"{actual}/{target}",
        "rationale": rationale,
        "command": command,
        "blocks_beta": True,
    }


def boolean_check(requirement_id, name, area, passed, detail, rationale, command, blocks_beta=True):
    return {
        "id": requirement_id,
        "name": name,
        "area": area,
        "status": "pass" if passed else "fail",
        "actual": passed,
        "target": True,
        "detail": detail,
        "rationale": rationale,
        "command": command,
        "blocks_beta": blocks_beta,
    }


def next_beta_moves(failed_checks, benchmark):
    moves = []
    failed_ids = {check["id"] for check in failed_checks}

    if "BETA-DATA-02" in failed_ids:
        missing = BETA_TARGETS["governed_modules"] - benchmark["module_seeded_count"]
        moves.append({
            "priority": "P1",
            "title": f"Seed {missing} more governed starter {pluralize('module', missing)}",
            "why": "A beta needs enough module variety to prove the library pattern.",
            "command": "python scripts/riskshard_modules.py countries",
        })

    if "BETA-DATA-03" in failed_ids:
        missing = BETA_TARGETS["benchmark_ready_candidates"] - benchmark["benchmark_ready_count"]
        moves.append({
            "priority": "P1",
            "title": f"Promote {missing} more {pluralize('module', missing)} to benchmark-ready candidates",
            "why": "The strongest public story needs multiple vetted examples, not one standout shard.",
            "command": "python scripts/benchmark_program.py --sprint seeded",
        })

    if "BETA-ENG-03" in failed_ids:
        moves.append({
            "priority": "P2",
            "title": "Record clean-install verification",
            "why": "Beta users should be able to install and run commands outside this working checkout.",
            "command": "python scripts/clean_install_proof.py --recreate",
        })

    for check in failed_checks:
        if check["id"] in {"BETA-DATA-02", "BETA-DATA-03", "BETA-ENG-03"}:
            continue
        moves.append({
            "priority": "P2",
            "title": f"Fix {check['name']}",
            "why": check["rationale"],
            "command": check["command"],
        })

    return moves


def pluralize(noun, count):
    return noun if count == 1 else f"{noun}s"


def format_beta_readiness_report(report):
    gate = report["gate"]
    lines = [
        "RiskShard beta readiness",
        f"Gate: {gate['status']} - {gate['summary']}",
        "",
        "Beta checks",
    ]

    for check in report["checks"]:
        status = check["status"].upper()
        lines.append(
            f"- {status} {check['id']} {check['name']}: {check['detail']}"
        )
        if check["status"] != "pass":
            lines.append(f"  why: {check['rationale']}")
            lines.append(f"  command: {check['command']}")

    lines.extend(["", "Next beta moves"])
    for move in report["next_beta_moves"]:
        lines.append(f"- {move['priority']} {move['title']}")
        lines.append(f"  why: {move['why']}")
        lines.append(f"  command: {move['command']}")

    lines.extend(["", "Deferred until beta"])
    for item in report["deferred_operating_model"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"
