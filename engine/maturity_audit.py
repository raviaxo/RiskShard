"""Maturity-label drift audit (backlog item 17, surfaced during F3a).

Each risk module carries a hand-maintained ``status`` label
(``governed_starter`` / ``benchmark_candidate`` / ``benchmark_review_candidate``).
The automated benchmark gate (``benchmark_program``) independently computes whether
a module is ``benchmark_ready``. These two drift: e.g. a module can clear the gate
yet still be labeled ``governed_starter``.

This module is a **read-only diagnostic**. It changes no labels — it only reports
where the hand-label and the machine gate disagree, so the maintainer can make the
Yellow decision recorded in ``docs/NEXT_STEPS.md`` item 17 (correct the labels, or
derive maturity from the gate so it cannot drift).
"""

from datetime import datetime
from pathlib import Path

from engine.benchmark_program import build_benchmark_program_report
from engine.risk_modules import load_risk_modules


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Labels that assert the module is at or near benchmark candidacy.
_BENCHMARK_CLAIMING_LABELS = {"benchmark_candidate", "benchmark_review_candidate"}


def classify(label, gate_status):
    """Pure classification of one module's label against the gate.

    Returns one of: ``consistent``, ``under_labeled`` (gate-ready but the label
    does not claim candidacy), ``over_labeled`` (label claims candidacy but the
    gate is not ready), or ``no_gate`` (module not evaluated by the gate).
    """
    if gate_status is None:
        return "no_gate"
    gate_ready = gate_status == "benchmark_ready"
    label_claims = label in _BENCHMARK_CLAIMING_LABELS
    if gate_ready and not label_claims:
        return "under_labeled"
    if label_claims and not gate_ready:
        return "over_labeled"
    return "consistent"


def audit_maturity_labels(root=PROJECT_ROOT):
    modules = load_risk_modules(root)
    program = build_benchmark_program_report(root)
    gate_by_id = {t["module_id"]: t.get("status") for t in program.get("targets", [])}

    rows = []
    for module in modules:
        label = module["status"]
        gate_status = gate_by_id.get(module["id"])
        rows.append({
            "id": module["id"],
            "label": label,
            "gate_status": gate_status,
            "verdict": classify(label, gate_status),
        })

    mismatches = [r for r in rows if r["verdict"] in ("under_labeled", "over_labeled")]
    # Vocabulary drift: more than one distinct benchmark-claiming label in use.
    claiming_labels = sorted({
        r["label"] for r in rows if r["label"] in _BENCHMARK_CLAIMING_LABELS
    })
    return {
        "report_type": "riskshard_maturity_audit",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "module_count": len(rows),
        "mismatch_count": len(mismatches),
        "vocabulary_labels_in_use": claiming_labels,
        "vocabulary_drift": len(claiming_labels) > 1,
        "modules": rows,
        "mismatches": mismatches,
    }


def format_maturity_audit(report):
    lines = [
        "RiskShard maturity-label audit (read-only; changes no labels)",
        f"Modules: {report['module_count']}; label/gate mismatches: {report['mismatch_count']}",
    ]
    if report["vocabulary_drift"]:
        lines.append(
            "Vocabulary drift: multiple benchmark-claiming labels in use -> "
            + ", ".join(report["vocabulary_labels_in_use"])
        )
    lines.append("")
    if report["mismatches"]:
        lines.append("Mismatches (label disagrees with the machine gate)")
        for row in report["mismatches"]:
            lines.append(
                f"- {row['id']}: label={row['label']} vs gate={row['gate_status']} "
                f"-> {row['verdict']}"
            )
    else:
        lines.append("No label/gate mismatches.")
    lines.extend([
        "",
        "This is a diagnostic. Correcting labels (or deriving maturity from the "
        "gate) is a Yellow decision -- see docs/NEXT_STEPS.md item 17.",
    ])
    return "\n".join(lines) + "\n"
