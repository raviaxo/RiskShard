"""Coverage / confidence rubric (Roadmap Lane 1, F3a).

Turns the per-shard signals already computed by the shard registry
(source-backed vs. assumption vs. missing direct parameters, pack confidence,
feed freshness, module maturity) into a single legible **data-strength grade**
plus a plain-language self-qualification line and a contribution funnel.

It invents no new signals and applies no thresholds beyond counting the existing
evidence-pack fields, so a shard's grade is a deterministic function of its
governed evidence. The rubric deliberately tops out at ``source_backed``: whether
a shard may be called benchmark-grade is a human decision recorded in
``docs/BENCHMARK_REVIEW_LEDGER.md``, never a machine grade. See
``docs/METHODOLOGY.md``.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.shard_registry import build_shard_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ordered strongest -> weakest. Each grade is defined purely by counting the
# existing direct-parameter statuses; the "fit" line is the user
# self-qualification ("can I use this number for my decision?").
GRADES = {
    "source_backed": {
        "rank": 0,
        "label": "source-backed",
        "fit": (
            "Suitable for expert practitioner review and internal risk framing. "
            "Not a human-approved benchmark; confirm the shard's caveats before "
            "external or capital/insurance use."
        ),
    },
    "bridged": {
        "rank": 1,
        "label": "assumption-bridged",
        "fit": (
            "Use for directional framing and internal discussion only, not "
            "capital or insurance decisions. Run `packs` to see which parameters "
            "are bridged or estimated."
        ),
    },
    "provisional": {
        "rank": 2,
        "label": "provisional",
        "fit": (
            "Not decision-ready: some parameters have no evidence at all. Use it "
            "to see the workflow, not to quote a number."
        ),
    },
    "scaffold": {
        "rank": 3,
        "label": "scaffold",
        "fit": "Do not use for any decision; this is a contribution scaffold.",
    },
}


def grade_shard(evidence_summary):
    """Grade one shard's data strength from its evidence summary.

    ``evidence_summary`` is the dict the shard registry already builds
    (``source_backed_direct``, ``assumption_only_direct``, ``missing_direct``,
    ``direct_total``, ``pack_confidence``, ``freshness_status``).

    The grade is a function of the governed evidence only. It deliberately does
    NOT read the module ``status`` label (which drifts and is hand-maintained)
    and does NOT claim benchmark status: "cleared the automated gate" is owned by
    ``benchmark_program``, and "benchmark-grade" is a human ledger decision.
    """
    total = evidence_summary.get("direct_total") or 0
    source_backed = evidence_summary.get("source_backed_direct", 0)
    assumptions = evidence_summary.get("assumption_only_direct", 0)
    missing = evidence_summary.get("missing_direct", 0)
    confidence = evidence_summary.get("pack_confidence", "none")
    freshness = evidence_summary.get("freshness_status", "unknown")

    if total == 0 or confidence == "none" or missing >= total:
        grade = "scaffold"
    elif missing > 0:
        grade = "provisional"
    elif source_backed < total:
        grade = "bridged"
    else:
        grade = "source_backed"

    label = GRADES[grade]["label"]
    if grade == "source_backed" and confidence in ("medium", "high"):
        label = f"{label} ({confidence} confidence)"

    flags = []
    if freshness == "needs_source_review":
        flags.append(
            "stale-feeds: at least one source is past its renewal date; refresh "
            "before quoting."
        )

    return {
        "grade": grade,
        "rank": GRADES[grade]["rank"],
        "label": label,
        "fit": GRADES[grade]["fit"],
        "flags": flags,
        "source_backed": source_backed,
        "assumptions": assumptions,
        "missing": missing,
        "total": total,
        "confidence": confidence,
        "freshness": freshness,
    }


def build_coverage_report(root=PROJECT_ROOT, module_id=None):
    registry = build_shard_registry(root)
    entries = registry["entries"]
    if module_id:
        entries = [entry for entry in entries if entry["id"] == module_id]

    graded = []
    for entry in entries:
        grade = grade_shard(entry["evidence_summary"])
        graded.append({
            "id": entry["id"],
            "title": entry["title"],
            "context": entry["context"],
            "threat": entry["threat"],
            "maturity": entry["maturity"],
            "grade": grade,
        })

    graded.sort(key=lambda item: (item["grade"]["rank"], item["id"]))
    grade_counts = Counter(item["grade"]["grade"] for item in graded)

    return {
        "report_type": "riskshard_coverage",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "shard_count": len(graded),
        "grade_counts": {name: grade_counts.get(name, 0) for name in GRADES},
        "shards": graded,
    }


def _context_label(context):
    return "/".join(
        str(context.get(field, "")) for field in ("country", "industry", "company_size")
    )


def format_coverage_report(report):
    lines = [
        "RiskShard coverage & confidence",
        f"Shards: {report['shard_count']}",
        "Grades: " + _format_grade_counts(report["grade_counts"]),
        "",
        "How to read the grade (data strength, not benchmark status):",
        "  source-backed     all 6 parameters trace to reviewed public sources.",
        "  assumption-bridged all present, but some are labeled bridges/estimates.",
        "  provisional       one or more parameters have no evidence yet.",
        "  scaffold          contribution placeholder; do not use the number.",
        "  No grade means benchmark-grade: that is a human decision in the ledger.",
        "  Automated gate status: python scripts/benchmark_program.py --cohort seeded",
        "",
        "Shards (strongest first)",
    ]
    for item in report["shards"]:
        grade = item["grade"]
        lines.append(
            f"- {item['id']}: {grade['label']} "
            f"[{grade['source_backed']}/{grade['total']} source-backed, "
            f"{grade['assumptions']} bridged, {grade['missing']} missing] "
            f"/ {_context_label(item['context'])} / {item['threat']}"
        )
        lines.append(f"    fit: {grade['fit']}")
        for flag in grade["flags"]:
            lines.append(f"    flag: {flag}")

    funnel = [
        item for item in report["shards"]
        if item["grade"]["grade"] in ("bridged", "provisional", "scaffold")
    ]
    lines.extend(["", "Where to contribute (weakest first)"])
    if funnel:
        for item in funnel:
            grade = item["grade"]
            gap = grade["missing"] + grade["assumptions"]
            lines.append(
                f"- {item['id']}: {gap} of {grade['total']} parameters need "
                f"stronger evidence -> python scripts/riskshard_modules.py "
                f"propose {item['id']}"
            )
    else:
        lines.append("- Every shard is fully source-backed; deepen confidence and freshness next.")

    return "\n".join(lines) + "\n"


def _format_grade_counts(counts):
    ordered = sorted(counts.items(), key=lambda kv: GRADES[kv[0]]["rank"])
    parts = [f"{GRADES[name]['label']}={count}" for name, count in ordered if count]
    return ", ".join(parts) or "none"
