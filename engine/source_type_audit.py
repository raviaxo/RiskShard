"""Audit source_type values against the canonical vocabulary (read-only).

A source_type is conformant if it is a `base` value in taxonomies/source_types.yaml,
or follows an honesty convention: a `<base>_bridge` suffix, a `derived_` prefix, or
`model_assumption`. Anything else is an unknown (typo or an un-vetted category).
Changes nothing; diagnostic only, matching engine/maturity_audit.py.
"""
from collections import Counter
from pathlib import Path

import yaml

from engine.evidence import load_evidence_records


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = PROJECT_ROOT / "taxonomies" / "source_types.yaml"


def load_source_type_taxonomy(path=TAXONOMY_PATH):
    with open(path) as handle:
        return yaml.safe_load(handle)


def classify_source_type(value, taxonomy):
    conventions = taxonomy["conventions"]
    if value in taxonomy["base"]:
        return "base"
    if value == conventions["assumption"]:
        return "assumption"
    if value.endswith(conventions["bridge_suffix"]):
        return "bridge"
    if value.startswith(conventions["derived_prefix"]):
        return "derived"
    return "unknown"


def collect_source_types(root=PROJECT_ROOT):
    counts = Counter()
    for record in load_evidence_records(Path(root) / "evidence"):
        source_type = record.get("source_type")
        if source_type:
            counts[source_type] += 1
    registry = yaml.safe_load((Path(root) / "sources" / "registry.yaml").read_text())
    for source in registry.get("sources", []):
        source_type = source.get("source_type")
        if source_type:
            counts[source_type] += 1
    return counts


def audit_source_types(root=PROJECT_ROOT):
    taxonomy = load_source_type_taxonomy()
    counts = collect_source_types(root)
    classification = {value: classify_source_type(value, taxonomy) for value in counts}
    by_kind = {
        kind: sorted(value for value, k in classification.items() if k == kind)
        for kind in ("base", "bridge", "derived", "assumption", "unknown")
    }
    return {
        "total_distinct": len(counts),
        "counts": dict(counts),
        "classification": classification,
        "by_kind": by_kind,
        "unknown": by_kind["unknown"],
    }


def format_source_type_audit(report):
    lines = [
        "RiskShard source_type vocabulary audit (read-only; changes nothing)",
        "",
        f"Distinct source_type values: {report['total_distinct']}",
    ]
    for kind in ("base", "bridge", "derived", "assumption", "unknown"):
        lines.append(f"- {kind}: {len(report['by_kind'][kind])}")
    if report["unknown"]:
        lines.append("")
        lines.append(
            "Unknown values (not a base type and not a bridge/derived/assumption convention):"
        )
        for value in report["unknown"]:
            lines.append(f"- {value}  x{report['counts'][value]}")
        lines.append("")
        lines.append(
            "Add each to the taxonomies/source_types.yaml base list, rename to a "
            "convention (_bridge / derived_ / model_assumption), or reconcile a duplicate."
        )
    else:
        lines.append("")
        lines.append(
            "All source_type values conform to the vocabulary (base type or a "
            "bridge/derived/assumption convention)."
        )
    return "\n".join(lines) + "\n"
