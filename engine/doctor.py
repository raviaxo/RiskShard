import platform
import subprocess
import sys
from pathlib import Path

from engine.contributor import build_contributor_preflight
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.extractions import validate_extractions
from engine.governance import build_data_feed_inventory
from engine.readiness import build_readiness_dashboard
from engine.scenarios import summarize_scenario_stages
from engine.sources import active_sources, load_source_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ENTRY_POINTS = {
    "riskshard",
    "riskshard-calibrate",
    "riskshard-console",
    "riskshard-web-console",
    "riskshard-feeds",
    "riskshard-readiness",
    "riskshard-data-pack",
    "riskshard-preflight",
    "riskshard-doctor",
}


def build_doctor_report(root=PROJECT_ROOT, *, run_tests=False):
    root = Path(root)
    checks = [
        environment_check(root),
        source_check(root),
        evidence_check(root),
        extraction_check(root),
        scenario_check(root),
        readiness_check(root),
        package_check(root),
        data_pack_check(root),
        tests_check(root, run_tests=run_tests),
    ]
    return {
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "needs_review",
        "checks": checks,
    }


def environment_check(root):
    required = root / "requirements.txt"
    return {
        "name": "environment",
        "status": "pass" if required.exists() else "fail",
        "detail": (
            f"python {platform.python_version()} on {platform.system().lower()}; "
            f"requirements={'present' if required.exists() else 'missing'}"
        ),
    }


def source_check(root):
    try:
        registry = load_source_registry(root / "sources" / "registry.yaml")
        active_count = len(active_sources(registry))
        inventory = build_data_feed_inventory(
            registry_path=root / "sources" / "registry.yaml",
            manifest_path=root / "sources" / "manifest.json",
            evidence_path=root / "evidence",
        )
        problem_count = len(inventory["feeds"]) - inventory["status_counts"].get("current", 0)
        status = "pass" if problem_count == 0 else "fail"
        detail = (
            f"{active_count} active of {len(registry['sources'])} registered; "
            f"feeds {format_counts(inventory['status_counts'])}"
        )
        return {"name": "sources", "status": status, "detail": detail}
    except Exception as exc:
        return {"name": "sources", "status": "fail", "detail": str(exc)}


def evidence_check(root):
    issues = validate_evidence_quality(root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "name": "evidence",
        "status": "fail" if has_errors(issues) else "pass",
        "detail": f"{len(errors)} error(s), {len(warnings)} warning(s)",
    }


def extraction_check(root):
    issues = validate_extractions(root / "extractions", root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "name": "extractions",
        "status": "fail" if errors else "pass",
        "detail": f"{len(errors)} error(s), {len(warnings)} warning(s)",
    }


def scenario_check(root):
    try:
        counts = summarize_scenario_stages(root)
        return {
            "name": "scenarios",
            "status": "pass",
            "detail": format_counts(counts),
        }
    except Exception as exc:
        return {"name": "scenarios", "status": "fail", "detail": str(exc)}


def readiness_check(root):
    dashboard = build_readiness_dashboard(root, root / "org_profiles" / "au_finance_midmarket.yaml")
    gate = dashboard["readiness_gate"]
    return {
        "name": "readiness",
        "status": "pass" if gate["status"] == "ready_for_local_calibrated_run" else "fail",
        "detail": f"{gate['status']} - {gate['summary']}",
    }


def package_check(root):
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return {"name": "package entry points", "status": "fail", "detail": "pyproject.toml missing"}

    configured = parse_project_scripts(pyproject.read_text())
    missing = sorted(EXPECTED_ENTRY_POINTS - set(configured))
    status = "pass" if not missing else "fail"
    detail = (
        f"{len(configured)} configured"
        if not missing
        else "missing " + ", ".join(missing)
    )
    return {"name": "package entry points", "status": status, "detail": detail}


def parse_project_scripts(text):
    scripts = []
    in_scripts = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts and line.startswith("["):
            break
        if in_scripts and "=" in line:
            scripts.append(line.split("=", 1)[0].strip())
    return scripts


def data_pack_check(root):
    preflight = build_contributor_preflight(root)
    pack = next((item for item in preflight["checks"] if item["name"] == "data pack fingerprint"), None)
    return {
        "name": "data pack",
        "status": pack["status"] if pack else "fail",
        "detail": pack["detail"] if pack else "missing data pack check",
    }


def tests_check(root, *, run_tests=False):
    test_files = sorted((root / "tests").glob("test_*.py"))
    if not run_tests:
        return {
            "name": "tests",
            "status": "pass" if test_files else "fail",
            "detail": f"{len(test_files)} test files; run with --run-tests for full suite",
        }

    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    summary = last_non_empty_line(result.stderr or result.stdout)
    return {
        "name": "tests",
        "status": "pass" if result.returncode == 0 else "fail",
        "detail": summary or f"return code {result.returncode}",
    }


def last_non_empty_line(text):
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.strip()
    return ""


def format_doctor_report(report):
    lines = [
        "RiskShard doctor",
        f"Status: {report['status']}",
        "",
    ]
    for item in report["checks"]:
        lines.append(f"- {item['name']}: {item['status']} ({item['detail']})")
    return "\n".join(lines) + "\n"


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"
