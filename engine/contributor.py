from pathlib import Path

from engine.data_packs import build_data_pack_manifest
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.extractions import validate_extractions
from engine.sources import load_source_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def build_contributor_preflight(root=PROJECT_ROOT):
    root = Path(root)
    checks = []

    checks.append(source_registry_check(root))
    checks.append(evidence_quality_check(root))
    checks.append(extraction_mapping_check(root))
    checks.append(docs_check(root))
    checks.append(data_pack_check(root))

    return {
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "needs_review",
        "checks": checks,
    }


def source_registry_check(root):
    try:
        registry = load_source_registry(root / "sources" / "registry.yaml")
        return {
            "name": "source registry",
            "status": "pass",
            "detail": f"{len(registry['sources'])} registered sources",
        }
    except Exception as exc:
        return {"name": "source registry", "status": "fail", "detail": str(exc)}


def evidence_quality_check(root):
    issues = validate_evidence_quality(root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "name": "evidence quality",
        "status": "fail" if has_errors(issues) else "pass",
        "detail": f"{len(errors)} error(s), {len(warnings)} warning(s)",
    }


def extraction_mapping_check(root):
    issues = validate_extractions(root / "extractions", root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return {
        "name": "extraction mappings",
        "status": "fail" if errors else "pass",
        "detail": f"{len(errors)} error(s), {len(warnings)} warning(s)",
    }


def docs_check(root):
    required = [
        root / "docs" / "CONTRIBUTING.md",
        root / "docs" / "GLOBAL_READINESS_ROADMAP.md",
        root / "docs" / "CONSOLE_EXPERIENCE.md",
    ]
    missing = [path.relative_to(root).as_posix() for path in required if not path.exists()]
    return {
        "name": "contributor docs",
        "status": "fail" if missing else "pass",
        "detail": "missing " + ", ".join(missing) if missing else "required docs present",
    }


def data_pack_check(root):
    manifest = build_data_pack_manifest(root)
    return {
        "name": "data pack fingerprint",
        "status": "pass",
        "detail": f"{manifest['file_count']} files, fingerprint {manifest['fingerprint'][:12]}",
    }


def format_contributor_preflight(preflight):
    lines = [
        "Contributor preflight",
        f"Status: {preflight['status']}",
        "",
    ]
    for item in preflight["checks"]:
        lines.append(f"- {item['name']}: {item['status']} ({item['detail']})")
    return "\n".join(lines) + "\n"
