import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.evidence_packs import build_evidence_pack_registry
from engine.risk_modules import REQUIRED_ARTIFACTS, REQUIRED_PARAMETERS, load_risk_modules


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_shard_registry(root=PROJECT_ROOT):
    root = Path(root)
    modules = load_risk_modules(root)
    pack_registry = build_evidence_pack_registry(root)
    packs_by_module = {
        pack["module_id"]: pack
        for pack in pack_registry["packs"]
    }
    entries = [
        build_registry_entry(module, packs_by_module.get(module["id"]))
        for module in modules
    ]

    return {
        "registry_type": "riskshard_registry",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "module_count": len(entries),
        "maturity_counts": dict(sorted(Counter(entry["maturity"] for entry in entries).items())),
        "threat_counts": dict(sorted(Counter(entry["threat"] for entry in entries).items())),
        "context_counts": {
            "countries": dict(sorted(Counter(entry["context"]["country"] for entry in entries).items())),
            "industries": dict(sorted(Counter(entry["context"]["industry"] for entry in entries).items())),
            "company_sizes": dict(sorted(Counter(entry["context"]["company_size"] for entry in entries).items())),
        },
        "contract": shard_pack_contract(),
        "entries": entries,
    }


def build_registry_entry(module, pack):
    direct = pack["direct_parameters"] if pack else []
    source_backed = count_direct(direct, "source_backed")
    assumption_only = count_direct(direct, "assumption_only")
    missing = count_direct(direct, "missing")
    return {
        "id": module["id"],
        "title": module["title"],
        "version": module["version"],
        "maturity": module["status"],
        "threat": module["threat"],
        "context": module["context"],
        "description": module.get("description", ""),
        "tags": module.get("tags", []),
        "source_file": module.get("_source_file"),
        "artifacts": module["artifacts"],
        "required_parameters": module.get("required_parameters") or list(REQUIRED_PARAMETERS),
        "evidence_summary": {
            "record_count": pack["record_count"] if pack else 0,
            "source_count": pack["source_count"] if pack else 0,
            "source_backed_direct": source_backed,
            "assumption_only_direct": assumption_only,
            "missing_direct": missing,
            "direct_total": len(direct),
            "pack_confidence": pack["pack_confidence"] if pack else "none",
            "freshness_status": pack["freshness_status"] if pack else "unknown",
        },
        "commands": {
            "consume": [
                f"python scripts/riskshard_modules.py info {module['id']}",
                f"python scripts/riskshard_modules.py packs {module['id']}",
                "python scripts/riskshard_console.py",
            ],
            "enhance": [
                f"python scripts/riskshard_modules.py propose {module['id']}",
                f"python scripts/benchmark_program.py --target {module['id']}",
                "python scripts/contributor_preflight.py path/to/proposed_pack",
            ],
        },
        "practitioner_notes": module.get("practitioner_notes", {}),
    }


def shard_pack_contract():
    return {
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "required_parameters": list(REQUIRED_PARAMETERS),
        "expected_layout": [
            "sources/registry.yaml",
            "evidence/*.yaml",
            "extractions/*.yaml",
            "calibrations/*.yaml",
            "risk_modules/*.yaml",
            "scenarios/*.yaml",
            "org_profiles/*.yaml",
            "README.md",
        ],
        "review_commands": [
            "python scripts/contributor_preflight.py path/to/proposed_pack",
            "python scripts/riskshard_modules.py registry",
            "python scripts/benchmark_program.py --sprint seeded",
            "python -m unittest discover -s tests",
        ],
    }


def count_direct(direct_parameters, status):
    return sum(1 for item in direct_parameters if item["status"] == status)


def write_shard_registry(registry, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return output_path


def format_shard_registry(registry):
    lines = [
        "RiskShard registry",
        f"Modules: {registry['module_count']}",
        "Maturity: " + format_counts(registry["maturity_counts"]),
        "Threats : " + format_counts(registry["threat_counts"]),
        "",
        "Shard packs",
    ]
    for entry in registry["entries"]:
        evidence = entry["evidence_summary"]
        context = entry["context"]
        lines.extend([
            (
                f"- {entry['id']}: {entry['maturity']} / "
                f"{context['country']}/{context['industry']}/{context['company_size']} / "
                f"{entry['threat']}"
            ),
            (
                f"  evidence: {evidence['source_backed_direct']}/{evidence['direct_total']} "
                f"direct source-backed; assumptions={evidence['assumption_only_direct']}; "
                f"missing={evidence['missing_direct']}; confidence={evidence['pack_confidence']}"
            ),
            f"  consume: riskshard_modules.py info {entry['id']} -> packs {entry['id']}",
            f"  enhance: riskshard_modules.py propose {entry['id']}",
        ])
    return "\n".join(lines) + "\n"


def format_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in counts.items())
