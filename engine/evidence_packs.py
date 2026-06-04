from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.evidence import load_evidence_records
from engine.governance import build_data_feed_inventory
from engine.risk_modules import REQUIRED_PARAMETERS, find_risk_module, load_risk_modules


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIDENCE_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}


def build_evidence_pack_registry(root=PROJECT_ROOT, module_id=None):
    root = Path(root)
    modules = load_risk_modules(root)
    if module_id:
        module = find_risk_module(module_id, root)
        modules = [module] if module else []

    feed_inventory = build_data_feed_inventory(
        registry_path=root / "sources" / "registry.yaml",
        manifest_path=root / "sources" / "manifest.json",
        evidence_path=root / "evidence",
    )
    feeds_by_id = {feed["id"]: feed for feed in feed_inventory["feeds"]}
    packs = [
        build_evidence_pack(module, root, feeds_by_id)
        for module in modules
    ]

    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "pack_count": len(packs),
        "packs": packs,
    }


def build_evidence_pack(module, root=PROJECT_ROOT, feeds_by_id=None):
    root = Path(root)
    feeds_by_id = feeds_by_id or {}
    records = load_module_evidence_records(module, root)
    source_ids = sorted(source_ids_for_records(records))
    sources = [
        summarize_source(source_id, feeds_by_id.get(source_id))
        for source_id in source_ids
    ]
    direct = direct_parameter_summary(records, module.get("required_parameters") or REQUIRED_PARAMETERS)
    type_counts = Counter(record["evidence_type"] for record in records)
    confidence_counts = Counter(record["confidence"] for record in records)
    confidence = pack_confidence(direct, records)
    freshness = pack_freshness(sources)

    return {
        "module_id": module["id"],
        "title": module["title"],
        "status": module["status"],
        "threat": module["threat"],
        "context": module["context"],
        "evidence_files": module["artifacts"].get("evidence", []),
        "extraction_files": module["artifacts"].get("extractions", []),
        "record_count": len(records),
        "evidence_type_counts": dict(sorted(type_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "pack_confidence": confidence,
        "freshness_status": freshness,
        "direct_parameters": direct,
        "source_count": len(sources),
        "sources": sources,
    }


def load_module_evidence_records(module, root=PROJECT_ROOT):
    root = Path(root)
    records = []
    for evidence_path in module["artifacts"].get("evidence", []):
        records.extend(load_evidence_records(root / evidence_path))
    return records


def source_ids_for_records(records):
    source_ids = set()
    for record in records:
        for source_id in record.get("source_ids") or [record.get("source_id")]:
            if source_id:
                source_ids.add(source_id)
    return source_ids


def summarize_source(source_id, feed):
    if feed is None:
        return {
            "id": source_id,
            "title": None,
            "trust_tier": "unknown",
            "renewal_status": "unknown",
            "publication_date": None,
            "source_gathered_at": None,
            "riskshard_evidence_ingested_at": None,
            "renewal_due": None,
            "evidence_record_count": 0,
            "evidence_confidence": "none",
        }

    return {
        "id": source_id,
        "title": feed["title"],
        "trust_tier": feed["trust_tier"],
        "renewal_status": feed["renewal_status"],
        "publication_date": feed["publication_date"],
        "source_gathered_at": feed["source_gathered_at"],
        "riskshard_evidence_ingested_at": feed["riskshard_evidence_ingested_at"],
        "renewal_due": feed["renewal_due"],
        "evidence_record_count": feed["evidence_record_count"],
        "evidence_confidence": feed["evidence_confidence"],
    }


def direct_parameter_summary(records, required_parameters):
    by_parameter = {}
    for record in records:
        parameter = record["parameter"]
        if parameter not in required_parameters:
            continue
        by_parameter.setdefault(parameter, []).append(record)

    rows = []
    for parameter in required_parameters:
        candidates = by_parameter.get(parameter, [])
        source_backed = [record for record in candidates if record["evidence_type"] == "source_backed"]
        estimated = [record for record in candidates if record["evidence_type"] != "source_backed"]
        if not candidates:
            status = "missing"
        elif source_backed:
            status = "source_backed"
        else:
            status = "assumption_only"
        best = best_record(candidates)
        rows.append({
            "parameter": parameter,
            "status": status,
            "candidate_count": len(candidates),
            "source_backed_count": len(source_backed),
            "estimated_count": len(estimated),
            "best_evidence_id": best["id"] if best else None,
            "best_confidence": best["confidence"] if best else None,
        })
    return rows


def best_record(records):
    if not records:
        return None
    return sorted(
        records,
        key=lambda record: (
            record["evidence_type"] != "source_backed",
            -CONFIDENCE_RANK[record["confidence"]],
            record["id"],
        ),
    )[0]


def pack_confidence(direct_parameters, records):
    if any(item["status"] == "missing" for item in direct_parameters):
        return "low"
    if any(item["status"] == "assumption_only" for item in direct_parameters):
        return "low"
    if any(record["confidence"] == "low" for record in records):
        return "medium"
    return "high"


def pack_freshness(sources):
    statuses = {source["renewal_status"] for source in sources}
    if not statuses:
        return "no_source_backed_records"
    if statuses - {"current"}:
        return "needs_source_review"
    return "current"


def format_evidence_pack_registry(registry):
    lines = ["Evidence packs", ""]
    for pack in registry["packs"]:
        counts = format_counts(pack["evidence_type_counts"])
        lines.extend([
            f"- {pack['module_id']}: {pack['freshness_status']} / confidence={pack['pack_confidence']}",
            f"  records: {pack['record_count']} ({counts}); sources: {pack['source_count']}",
            (
                "  direct: "
                f"{direct_count(pack, 'source_backed')} source-backed, "
                f"{direct_count(pack, 'assumption_only')} assumption-only, "
                f"{direct_count(pack, 'missing')} missing"
            ),
        ])
    if not registry["packs"]:
        lines.append("No matching evidence packs.")
    return "\n".join(lines) + "\n"


def format_evidence_pack_detail(pack):
    lines = [
        f"Evidence pack: {pack['module_id']}",
        f"Title       : {pack['title']}",
        f"Threat      : {pack['threat']}",
        f"Status      : {pack['status']}",
        f"Freshness   : {pack['freshness_status']}",
        f"Confidence  : {pack['pack_confidence']}",
        f"Records     : {pack['record_count']} ({format_counts(pack['evidence_type_counts'])})",
        "",
        "Direct parameters",
    ]
    for item in pack["direct_parameters"]:
        lines.append(
            f"- {item['parameter']}: {item['status']} "
            f"candidates={item['candidate_count']} best={item['best_evidence_id'] or 'none'}"
        )

    lines.extend(["", "Sources"])
    for source in pack["sources"]:
        lines.append(
            f"- {source['id']}: {source['renewal_status']} trust={source['trust_tier']} "
            f"published={source['publication_date']} source_gathered={source['source_gathered_at'] or 'never'} "
            f"evidence_ingested={source['riskshard_evidence_ingested_at'] or 'none'} "
            f"renewal_due={source['renewal_due'] or 'n/a'}"
        )
    return "\n".join(lines) + "\n"


def direct_count(pack, status):
    return sum(1 for item in pack["direct_parameters"] if item["status"] == status)


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"
