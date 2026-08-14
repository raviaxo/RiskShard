import platform
import subprocess
import sys
from pathlib import Path

from engine.contributor import build_contributor_preflight
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.extractions import validate_extractions
from engine.governance import build_data_feed_inventory
from engine.package_smoke import (
    DEFAULT_EXPECTED_ENTRY_POINTS,
    build_package_smoke_report,
    parse_project_scripts,
)
from engine.readiness import build_readiness_dashboard
from engine.scenarios import summarize_scenario_stages
from engine.sources import active_sources, load_source_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ENTRY_POINTS = DEFAULT_EXPECTED_ENTRY_POINTS


def build_doctor_report(root=PROJECT_ROOT, *, run_tests=False):
    root = Path(root)
    checks = [
        environment_check(root),
        source_check(root),
        evidence_check(root),
        extraction_check(root),
        scenario_check(root),
        calibration_drift_check(root),
        url_stability_check(root),
        readiness_check(root),
        package_check(root),
        data_pack_check(root),
        loss_event_check(root),
        ledger_check(root),
        tests_check(root, run_tests=run_tests),
    ]
    return {
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "needs_review",
        "checks": checks,
    }


def loss_event_check(root):
    """ADR-0012: the registry is a bounded trial, so its state is reported every run.

    The two trial numbers are surfaced deliberately. The kill criterion is that if no
    shard cites an entry and nobody outside contributes one within two release cycles,
    the registry is retired rather than carried — and a criterion nobody can see is a
    criterion nobody applies.
    """
    from engine.loss_events import (
        citation_candidates,
        registry_summary,
        trial_metrics,
        validate_loss_events,
    )

    errors = validate_loss_events(root)
    summary = registry_summary(root)
    if not summary["events"]:
        return {
            "name": "loss events",
            "status": "pass",
            "detail": "registry empty (ADR-0012 trial not started)",
        }
    trial = trial_metrics(root)
    # "0 shards cite an entry" is only a retirement signal if some shard COULD. Report
    # both, so nobody reads "nothing fits yet" as "nobody bothered".
    candidates = citation_candidates(root)
    citable = sum(1 for c in candidates if c["citable"])
    blocked = sum(1 for c in candidates if c["blocked_by_exceedance_loss"])
    detail = (
        f"{summary['events']} events, {summary['amounts']} typed amounts "
        f"({summary['non_loss_amounts']} are recoveries/settlements/deltas, not event costs); "
        f"trial: {trial['shards_citing_a_registry_entry']} of {len(candidates)} shards cite an "
        f"entry, {citable} could"
        + (f" ({blocked} blocked: swapping would lose an exceedance statement)" if blocked else "")
    )
    if errors:
        return {
            "name": "loss events",
            "status": "fail",
            "detail": f"{len(errors)} error(s): {errors[0]}",
        }
    return {"name": "loss events", "status": "pass", "detail": detail}


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



def calibration_drift_check(root):
    """Do the numbers a shard simulates still match the evidence it displays?

    A scenario file carries the values the Monte Carlo actually runs, while the
    calibration derives them from selected evidence. Nothing kept the two in step, so a
    scenario could silently keep starter assumptions while the explorer displayed
    source-backed evidence beside a loss range that evidence never produced. Found
    2026-07-30 with five shards adrift.

    Gating since 2026-07-30, once the four drifted shards were corrected. It was
    introduced non-gating because correcting a drifted scenario moves a published number
    and that was an owner decision; with the backlog cleared, any new drift is a defect
    rather than a known state, and should fail.
    """
    import re as _re
    import yaml as _yaml
    from engine.web_console import WebConsoleApp

    def _close(a, b):
        """Effectively exact: a scenario value is written from calibration output.

        An earlier version used max(1.0, 2%) as the tolerance, which silently exempted
        every frequency value -- probabilities are all below 1, so the absolute floor of
        1.0 swallowed any drift. Only impact was ever checked.
        """
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            return False
        return abs(a - b) <= max(1e-9, 1e-6 * abs(b))

    drifted = []
    checked = 0
    try:
        for path in sorted((root / "risk_modules").glob("*.yaml")):
            module = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            artifacts = module.get("artifacts") or {}
            if not {"scenario", "calibration"} <= set(artifacts):
                continue
            scenario = _yaml.safe_load((root / artifacts["scenario"]).read_text(encoding="utf-8")) or {}
            app = WebConsoleApp(root=root)
            app.run_command(f"use {module['id']}")
            output = app.run_command("calibrate")["output"]
            checked += 1
            for block in ("Frequency", "Impact"):
                found = _re.search(rf"{block}\s*:\s*(\{{.*?\}})", output)
                if not found:
                    continue
                calibrated = _yaml.safe_load(found.group(1).replace("'", '"'))
                current = scenario.get(block.lower(), {})
                if any(not _close(current.get(k), v) for k, v in calibrated.items()):
                    drifted.append(f"{module['id']}/{block.lower()}")
        # Top-risk scenarios sit outside the risk-module artifact graph, which is
        # how the insider scenario once drifted invisibly (found 2026-08-01, fixed
        # same day, gap left open). A calibration that maintains such a scenario
        # declares the pairing in `metadata.drift_watch`; every declared pair is
        # held to the same effectively-exact standard as the module shards.
        from engine.calibration import run_calibration

        for path in sorted((root / "calibrations").glob("*.yaml")):
            profile = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            watch = (profile.get("metadata") or {}).get("drift_watch") or {}
            if not {"scenario", "org_profile", "threat"} <= set(watch):
                continue
            report = run_calibration(
                root / watch["scenario"],
                root / watch["org_profile"],
                root / "evidence",
                path,
                threat=watch["threat"],
            )
            generated = report["generated_scenario"]
            scenario = _yaml.safe_load((root / watch["scenario"]).read_text(encoding="utf-8")) or {}
            checked += 1
            for block in ("frequency", "impact"):
                current = scenario.get(block, {})
                calibrated = generated.get(block, {})
                if any(not _close(current.get(k), v) for k, v in calibrated.items()):
                    drifted.append(f"toprisk:{Path(watch['scenario']).stem}/{block}")
        if not checked:
            return {"name": "calibration drift", "status": "pass", "detail": "no calibrated shards"}
        if drifted:
            return {
                "name": "calibration drift",
                "status": "fail",
                "detail": (f"{len(drifted)} of {checked * 2} scenario blocks no longer match "
                           f"their calibration and are simulating stale values "
                           f"({', '.join(drifted)}); the loss range shown would not be "
                           f"produced by the evidence displayed beside it"),
            }
        return {"name": "calibration drift", "status": "pass",
                "detail": f"{checked} scenario/calibration pairs match (risk-module shards + drift_watch top-risk scenarios)"}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": "calibration drift", "status": "fail", "detail": str(exc)}



def url_stability_check(root):
    """How many source URLs are known to be edition-stable.

    Reported, never gated. A `rolling` URL is not a defect -- it is a fact about the
    publisher that means the artifact will drift away from the citation and the record
    needs re-verifying when it does. `unknown` means nobody has looked yet, which is the
    honest default rather than an assumption of stability.

    Prompted by ibm.com/reports/data-breach silently serving the 2026 edition under a
    record citing the 2025 figure (2026-07-31). The content-type guard could not catch it:
    HTML was still HTML.
    """
    import yaml as _yaml

    try:
        registry = _yaml.safe_load((root / "sources" / "registry.yaml").read_text(encoding="utf-8"))
        sources = registry["sources"] if isinstance(registry, dict) else registry
        counts = {"dated": 0, "rolling": 0, "unknown": 0}
        rolling = []
        for source in sources:
            value = source.get("url_stability", "unknown")
            counts[value] = counts.get(value, 0) + 1
            if value == "rolling":
                rolling.append(source["id"])
        detail = (f"{counts['dated']} dated, {counts['rolling']} rolling, "
                  f"{counts['unknown']} unassessed of {len(sources)}")
        if rolling:
            detail += f"; re-verify citations for: {', '.join(sorted(rolling))}"
        return {"name": "source url stability", "status": "pass", "detail": detail}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": "source url stability", "status": "fail", "detail": str(exc)}


def readiness_check(root):
    dashboard = build_readiness_dashboard(root, root / "org_profiles" / "au_finance_midmarket.yaml")
    gate = dashboard["readiness_gate"]
    return {
        "name": "readiness",
        "status": "pass" if gate["status"] == "ready_for_local_calibrated_run" else "fail",
        "detail": f"{gate['status']} - {gate['summary']}",
    }


def package_check(root):
    report = build_package_smoke_report(root, expected_entry_points=EXPECTED_ENTRY_POINTS)
    passed = len([item for item in report["entry_points"] if item["status"] == "pass"])
    failures = [item for item in report["entry_points"] if item["status"] != "pass"]
    detail = f"{report['configured_count']} configured; {passed} importable callables"
    if failures:
        first = failures[0]
        detail = f"{detail}; first failure: {first['name']} - {first['detail']}"
    return {"name": "package entry points", "status": report["status"], "detail": detail}


def data_pack_check(root):
    preflight = build_contributor_preflight(root)
    pack = next((item for item in preflight["checks"] if item["name"] == "data pack fingerprint"), None)
    return {
        "name": "data pack",
        "status": pack["status"] if pack else "fail",
        "detail": pack["detail"] if pack else "missing data pack check",
    }


def ledger_check(root):
    """Flag when the current data pack's strength isn't yet in the progress ledger.

    Passing means the trend is caught up to what's shipped; needs_review means a
    release/evidence change happened without a ledger tick (run
    `scripts/strength_ledger.py record`, or cut the release which does it for you).
    """
    try:
        from engine.data_packs import build_data_pack_manifest
        from engine.strength_ledger import LEDGER_RELPATH, latest_delta

        current_fp = build_data_pack_manifest(root).get("fingerprint", "")
        latest, _ = latest_delta(root / LEDGER_RELPATH)
        if latest is None:
            return {
                "name": "strength ledger",
                "status": "needs_review",
                "detail": "ledger empty - run scripts/strength_ledger.py record",
            }
        if latest.get("fingerprint") == current_fp:
            return {
                "name": "strength ledger",
                "status": "pass",
                "detail": f"caught up at {latest.get('data_pack_version', '?')} ({current_fp[:12]})",
            }
        return {
            "name": "strength ledger",
            "status": "needs_review",
            "detail": (
                f"current pack {current_fp[:12]} not logged "
                f"(latest entry {latest.get('fingerprint', '')[:12]}) - record on release"
            ),
        }
    except Exception as exc:  # never let the nudge crash the doctor
        return {"name": "strength ledger", "status": "needs_review", "detail": str(exc)}


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
