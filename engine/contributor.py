from pathlib import Path

from engine.data_packs import build_data_pack_manifest
from engine.evidence import load_evidence_records
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.extractions import load_extractions, validate_extractions
from engine.profiles import load_yaml_file
from engine.risk_modules import REQUIRED_ARTIFACTS, REQUIRED_FIELDS, REQUIRED_PARAMETERS
from engine.sources import load_source_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BENCHMARK_TARGET_PATH = PROJECT_ROOT / "benchmark_targets" / "benchmark_grade_30.yaml"
PACK_FILE_GROUPS = {
    "sources": ("sources/registry.yaml",),
    "evidence": ("evidence",),
    "extractions": ("extractions",),
    "calibrations": ("calibrations",),
    "risk_modules": ("risk_modules",),
}
PLACEHOLDER_MARKERS = ("REPLACE_ME", "scaffold placeholder", "placeholder before review")


def build_contributor_preflight(root=PROJECT_ROOT, pack_path=None):
    root = Path(root)
    if pack_path:
        return build_pack_preflight(root, pack_path)

    checks = [
        source_registry_check(root),
        evidence_quality_check(root),
        extraction_mapping_check(root),
        docs_check(root),
        data_pack_check(root),
    ]

    return {
        "status": aggregate_status(checks),
        "checks": checks,
    }


def build_pack_preflight(root, pack_path):
    root = Path(root)
    pack_root = resolve_pack_path(root, pack_path)
    context = load_pack_context(root, pack_root)
    checks = [
        pack_shape_check(root, pack_root),
        pack_source_check(context),
        pack_evidence_check(context),
        pack_extraction_check(context),
        pack_calibration_check(context),
        pack_module_check(context),
        pack_benchmark_target_check(context),
        pack_placeholder_check(pack_root),
        pack_docs_check(pack_root),
    ]
    return {
        "status": aggregate_status(checks),
        "pack_path": relative_to_root_or_cwd(pack_root, root),
        "checks": checks,
    }


def resolve_pack_path(root, pack_path):
    path = Path(pack_path)
    if not path.is_absolute():
        path = Path(root) / path
    return path


def load_pack_context(root, pack_root):
    root_sources, root_source_error = safe_load_sources(root / "sources" / "registry.yaml")
    pack_sources, pack_source_error = safe_load_sources(pack_root / "sources" / "registry.yaml")
    root_evidence, root_evidence_error = safe_load_evidence(root / "evidence")
    pack_evidence, pack_evidence_error = safe_load_evidence(pack_root / "evidence")
    root_source_ids = {source["id"] for source in root_sources}
    pack_source_ids = {source["id"] for source in pack_sources}
    root_evidence_ids = {record["id"] for record in root_evidence}
    pack_evidence_ids = {record["id"] for record in pack_evidence}
    sources_by_id = {
        source["id"]: source
        for source in [*root_sources, *pack_sources]
    }
    benchmark_targets, benchmark_target_error = safe_load_benchmark_targets(
        root / "benchmark_targets" / "benchmark_grade_30.yaml"
    )
    benchmark_targets_by_id = {target["id"]: target for target in benchmark_targets}
    benchmark_targets_by_module = {target["module_id"]: target for target in benchmark_targets}

    return {
        "root": Path(root),
        "pack_root": Path(pack_root),
        "root_sources": root_sources,
        "pack_sources": pack_sources,
        "root_source_error": root_source_error,
        "pack_source_error": pack_source_error,
        "root_evidence_error": root_evidence_error,
        "pack_evidence_error": pack_evidence_error,
        "root_source_ids": root_source_ids,
        "pack_source_ids": pack_source_ids,
        "sources_by_id": sources_by_id,
        "root_evidence": root_evidence,
        "pack_evidence": pack_evidence,
        "root_evidence_ids": root_evidence_ids,
        "pack_evidence_ids": pack_evidence_ids,
        "all_evidence_ids": root_evidence_ids | pack_evidence_ids,
        "benchmark_target_error": benchmark_target_error,
        "benchmark_targets_by_id": benchmark_targets_by_id,
        "benchmark_targets_by_module": benchmark_targets_by_module,
    }


def safe_load_sources(path):
    path = Path(path)
    if not path.exists():
        return [], None
    try:
        return load_source_registry(path)["sources"], None
    except Exception as exc:
        return [], str(exc)


def safe_load_evidence(path):
    path = Path(path)
    if not path.exists():
        return [], None
    try:
        return load_evidence_records(path), None
    except Exception as exc:
        return [], str(exc)


def safe_load_benchmark_targets(path=DEFAULT_BENCHMARK_TARGET_PATH):
    try:
        return load_yaml_file(path).get("targets", []), None
    except Exception as exc:
        return [], str(exc)


def pack_shape_check(root, pack_root):
    if not pack_root.exists():
        return check(
            "pack path",
            "fail",
            f"path does not exist: {relative_to_root_or_cwd(pack_root, root)}",
        )
    if not pack_root.is_dir():
        return check("pack path", "fail", "pack path must be a directory")

    present = []
    missing = []
    for name, paths in PACK_FILE_GROUPS.items():
        if any(pack_path_exists(pack_root, value) for value in paths):
            present.append(name)
        else:
            missing.append(name)

    status = "fail" if missing else "pass"
    detail = (
        f"present {', '.join(present)}"
        if not missing
        else f"missing {', '.join(missing)}; present {', '.join(present) or 'none'}"
    )
    return check("pack shape", status, detail)


def pack_path_exists(pack_root, value):
    path = pack_root / value
    if path.is_file():
        return True
    if path.is_dir():
        return any(path.rglob("*.yaml"))
    return False


def pack_source_check(context):
    if not (context["pack_root"] / "sources" / "registry.yaml").exists():
        return check(
            "pack sources",
            "warn",
            "no sources/registry.yaml in pack; evidence must reference existing repo sources",
        )
    if context["pack_source_error"]:
        return check("pack sources", "fail", context["pack_source_error"])
    pack_sources = context["pack_sources"]
    if not pack_sources:
        return check("pack sources", "fail", "sources/registry.yaml contains no sources")

    duplicate_ids = sorted(context["root_source_ids"] & context["pack_source_ids"])
    status = "fail" if duplicate_ids else "pass"
    detail = (
        f"{len(pack_sources)} proposed source(s)"
        if not duplicate_ids
        else "duplicate source id(s): " + ", ".join(duplicate_ids)
    )
    return check("pack sources", status, detail)


def pack_evidence_check(context):
    pack_evidence_dir = context["pack_root"] / "evidence"
    if not pack_evidence_dir.exists():
        return check("pack evidence", "fail", "missing evidence/*.yaml")
    if context["pack_evidence_error"]:
        return check("pack evidence", "fail", context["pack_evidence_error"])
    records = context["pack_evidence"]
    if not records:
        return check("pack evidence", "fail", "no evidence records found")

    issues = []
    duplicates = sorted(context["root_evidence_ids"] & context["pack_evidence_ids"])
    issues.extend(f"duplicate evidence id {evidence_id}" for evidence_id in duplicates)

    for record in records:
        record_id = record["id"]
        if record["unit"] == "currency" and not record.get("currency"):
            issues.append(f"{record_id}: currency evidence must include currency")
        if record["evidence_type"] != "source_backed":
            continue
        source_id = record.get("source_id")
        if not source_id:
            issues.append(f"{record_id}: source-backed evidence missing source_id")
            continue
        source = context["sources_by_id"].get(source_id)
        if source is None:
            issues.append(f"{record_id}: unknown source_id {source_id}")
            continue
        if not record.get("citation_detail"):
            issues.append(f"{record_id}: missing citation_detail")
        if record.get("publication_date") != source.get("publication_date"):
            issues.append(f"{record_id}: publication_date does not match source {source_id}")
        if record.get("source_url_or_citation") != source.get("url"):
            issues.append(f"{record_id}: source_url_or_citation does not match source URL")

    status = "fail" if issues else "pass"
    detail = f"{len(records)} record(s)" if not issues else truncate_issues(issues)
    return check("pack evidence", status, detail)


def pack_extraction_check(context):
    extraction_dir = context["pack_root"] / "extractions"
    if not extraction_dir.exists():
        return check("pack extractions", "fail", "missing extractions/*.yaml")
    try:
        extractions = load_extractions(extraction_dir)
    except Exception as exc:
        return check("pack extractions", "fail", str(exc))
    if not extractions:
        return check("pack extractions", "fail", "no extraction records found")

    issues = []
    for extraction in extractions:
        extraction_id = extraction["id"]
        source = context["sources_by_id"].get(extraction["source_id"])
        if source is None:
            issues.append(f"{extraction_id}: unknown source_id {extraction['source_id']}")
        elif extraction.get("publication_date") != source.get("publication_date"):
            issues.append(f"{extraction_id}: publication_date does not match source")
        for evidence_id in extraction["evidence_record_ids"]:
            if evidence_id not in context["all_evidence_ids"]:
                issues.append(f"{extraction_id}: missing evidence record {evidence_id}")

    status = "fail" if issues else "pass"
    detail = f"{len(extractions)} extraction(s)" if not issues else truncate_issues(issues)
    return check("pack extractions", status, detail)


def pack_calibration_check(context):
    calibration_files = yaml_files(context["pack_root"] / "calibrations")
    if not calibration_files:
        return check("pack calibration", "fail", "missing calibrations/*.yaml")

    issues = []
    selector_count = 0
    for path in calibration_files:
        try:
            profile = load_yaml_file(path)
        except Exception as exc:
            issues.append(f"{path.name}: {exc}")
            continue
        for group in ("frequency", "impact"):
            group_spec = profile.get("parameters", {}).get(group, {})
            for bound in ("min", "likely", "max"):
                selector = group_spec.get(bound)
                if selector is None:
                    issues.append(f"{path.name}: missing selector {group}.{bound}")
                    continue
                selector_count += 1
                evidence_id = selector.get("evidence_id")
                if evidence_id not in context["all_evidence_ids"]:
                    issues.append(f"{path.name}: selector {group}.{bound} references missing evidence {evidence_id}")

    status = "fail" if issues else "pass"
    detail = f"{len(calibration_files)} file(s), {selector_count} selector(s)" if not issues else truncate_issues(issues)
    return check("pack calibration", status, detail)


def pack_module_check(context):
    module_files = yaml_files(context["pack_root"] / "risk_modules")
    if not module_files:
        return check("pack risk module", "fail", "missing risk_modules/*.yaml")

    issues = []
    for path in module_files:
        try:
            module = load_yaml_file(path)
        except Exception as exc:
            issues.append(f"{path.name}: {exc}")
            continue
        for field in REQUIRED_FIELDS:
            if field not in module:
                issues.append(f"{path.name}: missing {field}")
        artifacts = module.get("artifacts", {})
        for field in REQUIRED_ARTIFACTS:
            if field not in artifacts:
                issues.append(f"{path.name}: missing artifacts.{field}")
        for field in ("industry", "country", "company_size"):
            if field not in module.get("context", {}):
                issues.append(f"{path.name}: missing context.{field}")
        required = tuple(module.get("required_parameters") or REQUIRED_PARAMETERS)
        missing_parameters = [parameter for parameter in REQUIRED_PARAMETERS if parameter not in required]
        if missing_parameters:
            issues.append(f"{path.name}: required_parameters missing {', '.join(missing_parameters)}")
        issues.extend(module_artifact_issues(context, path.name, artifacts))

    status = "fail" if issues else "pass"
    detail = f"{len(module_files)} module file(s)" if not issues else truncate_issues(issues)
    return check("pack risk module", status, detail)


def pack_benchmark_target_check(context):
    if context["benchmark_target_error"]:
        return check("benchmark target mapping", "fail", context["benchmark_target_error"])

    module_files = yaml_files(context["pack_root"] / "risk_modules")
    if not module_files:
        return check(
            "benchmark target mapping",
            "warn",
            "no risk module to map; pack risk module check reports the missing artifact",
        )

    matched = []
    issues = []
    for path in module_files:
        try:
            module = load_yaml_file(path)
        except Exception as exc:
            # Previously `continue`: a malformed risk module vanished from the mapping
            # instead of being reported, so this gate could pass while a module was
            # unreadable. Report it and move on.
            issues.append(f"{path.name}: could not be parsed ({exc.__class__.__name__})")
            continue
        module_id = module.get("id")
        target = (
            context["benchmark_targets_by_id"].get(module_id)
            or context["benchmark_targets_by_module"].get(module_id)
        )
        if target is None:
            issues.append(f"{path.name}: {module_id} is not in benchmark_grade_30 targets")
            continue
        matched.append(module_id)
        issues.extend(module_target_mismatch_issues(path.name, module, target))

    if issues:
        return check("benchmark target mapping", "warn", truncate_issues(issues))
    if matched:
        return check("benchmark target mapping", "pass", "mapped target(s): " + ", ".join(sorted(matched)))
    return check(
        "benchmark target mapping",
        "warn",
        "no proposed module maps to benchmark_grade_30 targets",
    )


def pack_placeholder_check(pack_root):
    if not pack_root.exists() or not pack_root.is_dir():
        return check("placeholder review", "warn", "pack path is not available for placeholder scan")

    hits = []
    for path in sorted(pack_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(errors="ignore")
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            hits.append(relative_to_root_or_cwd(path, pack_root))

    if hits:
        return check(
            "placeholder review",
            "warn",
            "replace scaffold placeholders in " + ", ".join(hits[:5]) + (f"; {len(hits) - 5} more" if len(hits) > 5 else ""),
        )
    return check("placeholder review", "pass", "no scaffold placeholders found")


def module_target_mismatch_issues(filename, module, target):
    issues = []
    module_context = module.get("context", {})
    target_context = target["context"]
    if module.get("threat") != target_context["threat"]:
        issues.append(f"{filename}: threat differs from benchmark target")
    for field in ("country", "industry", "company_size"):
        if module_context.get(field) != target_context[field]:
            issues.append(f"{filename}: context.{field} differs from benchmark target")
    return issues


def module_artifact_issues(context, filename, artifacts):
    issues = []
    for field in ("scenario", "org_profile", "calibration"):
        value = artifacts.get(field)
        if value and not artifact_exists(context, value):
            issues.append(f"{filename}: artifacts.{field} missing {value}")
    for field in ("evidence", "extractions", "controls"):
        for value in artifacts.get(field, []):
            if not artifact_exists(context, value):
                issues.append(f"{filename}: artifacts.{field} missing {value}")
    return issues


def artifact_exists(context, value):
    rel_path = Path(value)
    return (context["root"] / rel_path).exists() or (context["pack_root"] / rel_path).exists()


def pack_docs_check(pack_root):
    docs = [
        pack_root / "README.md",
        pack_root / "docs" / "README.md",
    ]
    if any(path.exists() for path in docs):
        return check("pack docs", "pass", "contributor notes present")
    return check(
        "pack docs",
        "warn",
        "missing README.md or docs/README.md explaining sources, limitations, and review notes",
    )


def yaml_files(path):
    path = Path(path)
    if not path.exists():
        return []
    return sorted(path.rglob("*.yaml"))


def source_registry_check(root):
    try:
        registry = load_source_registry(root / "sources" / "registry.yaml")
        return check("source registry", "pass", f"{len(registry['sources'])} registered sources")
    except Exception as exc:
        return check("source registry", "fail", str(exc))


def evidence_quality_check(root):
    issues = validate_evidence_quality(root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return check(
        "evidence quality",
        "fail" if has_errors(issues) else "pass",
        f"{len(errors)} error(s), {len(warnings)} warning(s)",
    )


def extraction_mapping_check(root):
    issues = validate_extractions(root / "extractions", root / "evidence", root / "sources" / "manifest.json")
    errors = [item for item in issues if item["severity"] == "error"]
    warnings = [item for item in issues if item["severity"] == "warning"]
    return check(
        "extraction mappings",
        "fail" if errors else "pass",
        f"{len(errors)} error(s), {len(warnings)} warning(s)",
    )


def docs_check(root):
    required = [
        root / "CONTRIBUTING.md",
        root / "docs" / "BENCHMARK_CONTRIBUTOR_WORKFLOW.md",
        root / "docs" / "CONSOLE_EXPERIENCE.md",
    ]
    missing = [path.relative_to(root).as_posix() for path in required if not path.exists()]
    return check(
        "contributor docs",
        "fail" if missing else "pass",
        "missing " + ", ".join(missing) if missing else "required docs present",
    )


def data_pack_check(root):
    manifest = build_data_pack_manifest(root)
    return check(
        "data pack fingerprint",
        "pass",
        f"{manifest['file_count']} files, fingerprint {manifest['fingerprint'][:12]}",
    )


def format_contributor_preflight(preflight):
    lines = [
        "Contributor preflight",
        f"Status: {preflight['status']}",
    ]
    if preflight.get("pack_path"):
        lines.append(f"Pack: {preflight['pack_path']}")
    lines.append("")
    for item in preflight["checks"]:
        lines.append(f"- {item['name']}: {item['status']} ({item['detail']})")
    return "\n".join(lines) + "\n"


def scaffold_contributor_pack(
    root,
    pack_path,
    module_id,
    country,
    industry,
    company_size,
    threat,
    title=None,
    currency="USD",
    status="governed_starter",
    force=False,
):
    root = Path(root)
    pack_root = resolve_pack_path(root, pack_path)
    if pack_root.exists() and any(pack_root.iterdir()) and not force:
        raise FileExistsError(
            f"pack path is not empty: {relative_to_root_or_cwd(pack_root, root)}; pass force=True to overwrite scaffold files"
        )

    title = title or title_from_module_id(module_id)
    source_id = f"{module_id}_source_replace_me"
    evidence_ids = {
        parameter: f"{module_id}_{parameter.replace('.', '_')}_replace_me"
        for parameter in REQUIRED_PARAMETERS
    }
    written = []
    for folder in [
        "sources",
        "evidence",
        "extractions",
        "calibrations",
        "risk_modules",
        "scenarios",
        "org_profiles",
    ]:
        (pack_root / folder).mkdir(parents=True, exist_ok=True)

    files = {
        "README.md": render_scaffold_readme(module_id, title),
        "sources/registry.yaml": render_scaffold_sources(source_id, title),
        f"evidence/{module_id}.yaml": render_scaffold_evidence(
            module_id, evidence_ids, country, industry, company_size, threat, currency
        ),
        f"extractions/{module_id}_reviewed.yaml": render_scaffold_extractions(
            module_id, source_id, evidence_ids, title
        ),
        f"calibrations/{module_id}.yaml": render_scaffold_calibration(module_id, title, evidence_ids, currency),
        f"scenarios/{module_id}.yaml": render_scaffold_scenario(title, currency),
        f"org_profiles/{module_id}.yaml": render_scaffold_org_profile(title, country, industry, company_size),
        f"risk_modules/{module_id}.yaml": render_scaffold_module(
            module_id,
            title,
            status,
            threat,
            country,
            industry,
            company_size,
        ),
    }
    for rel_path, content in files.items():
        path = pack_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written.append(path)

    return {
        "status": "created",
        "pack_path": relative_to_root_or_cwd(pack_root, root),
        "module_id": module_id,
        "file_count": len(written),
        "files": [relative_to_root_or_cwd(path, pack_root) for path in written],
        "next_commands": [
            f"python scripts/contributor_preflight.py {relative_to_root_or_cwd(pack_root, root)}",
            f"python scripts/riskshard_modules.py registry --output results/riskshard_registry.json",
        ],
    }


def format_scaffold_result(result):
    lines = [
        "Contributor shard pack scaffold",
        f"Status: {result['status']}",
        f"Pack  : {result['pack_path']}",
        f"Module: {result['module_id']}",
        "",
        "Files:",
    ]
    lines.extend(f"- {path}" for path in result["files"])
    lines.extend(["", "Next commands:"])
    lines.extend(f"- {command}" for command in result["next_commands"])
    lines.append("")
    lines.append("Replace every REPLACE_ME placeholder with reviewed source-backed evidence before benchmark claims.")
    return "\n".join(lines) + "\n"


def title_from_module_id(module_id):
    return module_id.replace("_", " ").title()


def render_scaffold_readme(module_id, title):
    return (
        f"# {title}\n\n"
        "This is a RiskShard contributor scaffold. It is structurally valid, but it is not source-backed yet.\n\n"
        "## Replace Before Review\n\n"
        "- REPLACE_ME source registry fields with reviewed public sources.\n"
        "- REPLACE_ME extraction facts with source-grounded facts and citation detail.\n"
        "- Estimated evidence records with source_backed records where possible.\n"
        "- Scenario ranges with calibration outputs after source review.\n\n"
        "## Review Commands\n\n"
        "```bash\n"
        f"python scripts/contributor_preflight.py path/to/{module_id}_pack\n"
        f"python scripts/riskshard_modules.py propose {module_id}\n"
        f"python scripts/benchmark_program.py --target {module_id}\n"
        "```\n"
    )


def render_scaffold_sources(source_id, title):
    return (
        "sources:\n"
        f"  - id: {source_id}\n"
        f"    title: REPLACE_ME source for {title}\n"
        "    publisher: REPLACE_ME publisher\n"
        "    source_type: official_statistics\n"
        "    url: https://example.com/replace-me\n"
        "    publication_date: '2026-01-01'\n"
        "    access_mode: public_html\n"
        "    intended_use: [risk_parameter_calibration]\n"
        "    usage_notes: REPLACE_ME with source scope, caveats, and extraction notes.\n"
    )


def render_scaffold_evidence(module_id, evidence_ids, country, industry, company_size, threat, currency):
    rows = ["records:"]
    for parameter in REQUIRED_PARAMETERS:
        unit = "currency" if parameter.startswith("impact") else "annual_probability"
        value = 100000 if unit == "currency" else 0.1
        currency_line = f"    currency: {currency}\n" if unit == "currency" else ""
        rows.append(
            f"  - id: {evidence_ids[parameter]}\n"
            f"    title: REPLACE_ME {parameter} evidence\n"
            f"    parameter: {parameter}\n"
            f"    value: {value}\n"
            f"    unit: {unit}\n"
            f"{currency_line}"
            "    source_name: RiskShard contributor scaffold placeholder\n"
            "    source_type: model_assumption\n"
            "    source_url_or_citation: REPLACE_ME with reviewed source URL or citation.\n"
            "    publication_date: '2026-01-01'\n"
            "    extraction_date: '2026-01-01'\n"
            "    extraction_notes: scaffold placeholder before review; replace with reviewed extraction notes.\n"
            "    normalization_notes: scaffold placeholder before review; replace with normalization notes.\n"
            "    limitations: Low-confidence scaffold estimate. Replace before benchmark or public claims.\n"
            "    confidence: low\n"
            "    evidence_type: estimated\n"
            "    applicability:\n"
            f"      industries: [{industry}]\n"
            f"      countries: [{country}]\n"
            f"      company_size_bands: [{company_size}]\n"
            f"      threats: [{threat}]\n"
        )
    return "\n".join(rows)


def render_scaffold_extractions(module_id, source_id, evidence_ids, title):
    evidence_lines = "\n".join(f"      - {evidence_id}" for evidence_id in evidence_ids.values())
    return (
        "extractions:\n"
        f"  - id: {module_id}_source_fact_replace_me\n"
        f"    source_id: {source_id}\n"
        f"    source_name: REPLACE_ME source for {title}\n"
        "    source_url_or_citation: https://example.com/replace-me\n"
        "    publication_date: '2026-01-01'\n"
        "    extraction_date: '2026-01-01'\n"
        "    citation_detail: REPLACE_ME with page, table, section, or exact source locator.\n"
        "    fact: REPLACE_ME with reviewed source fact.\n"
        "    value: 1\n"
        "    unit: count\n"
        "    normalization_notes: scaffold placeholder before review; explain transformations here.\n"
        "    limitations: scaffold placeholder before review; explain caveats here.\n"
        "    evidence_record_ids:\n"
        f"{evidence_lines}\n"
    )


def render_scaffold_calibration(module_id, title, evidence_ids, currency):
    return (
        "metadata:\n"
        f"  name: {title} calibration scaffold\n"
        f"  scenario_name: {title} - Calibrated Draft\n"
        "  version: '0.1'\n"
        "  notes: REPLACE_ME with source selection rationale and limitations.\n"
        f"target_currency: {currency}\n"
        "parameters:\n"
        "  frequency:\n"
        f"    min: {{evidence_id: {evidence_ids['frequency.min']}, transform: direct}}\n"
        f"    likely: {{evidence_id: {evidence_ids['frequency.likely']}, transform: direct}}\n"
        f"    max: {{evidence_id: {evidence_ids['frequency.max']}, transform: direct}}\n"
        "  impact:\n"
        f"    min: {{evidence_id: {evidence_ids['impact.min']}, transform: direct, target_currency: {currency}}}\n"
        f"    likely: {{evidence_id: {evidence_ids['impact.likely']}, transform: direct, target_currency: {currency}}}\n"
        f"    max: {{evidence_id: {evidence_ids['impact.max']}, transform: direct, target_currency: {currency}}}\n"
    )


def render_scaffold_scenario(title, currency):
    return (
        "metadata:\n"
        f"  name: {title}\n"
        "  version: '0.1'\n"
        f"  currency: {currency}\n"
        "  scenario_stage: governed_starter\n"
        "  benchmark_status: scaffold_placeholder\n"
        "  description: REPLACE_ME with scenario scope, source basis, and limitations.\n"
        "frequency: {min: 0.01, likely: 0.10, max: 0.30}\n"
        "impact: {min: 10000, likely: 100000, max: 1000000}\n"
    )


def render_scaffold_org_profile(title, country, industry, company_size):
    return (
        "metadata:\n"
        f"  name: {title} Default Org Profile\n"
        "  version: '0.1'\n"
        "org_type: private_company\n"
        f"industry: {industry}\n"
        f"country: {country}\n"
        "employees: 500\n"
        "annual_revenue_or_budget: 100000000\n"
        f"company_size: {company_size}\n"
        "data_sensitivity: REPLACE_ME\n"
        "internet_exposure: REPLACE_ME\n"
        "third_party_dependency: REPLACE_ME\n"
        "regulatory_intensity: REPLACE_ME\n"
    )


def render_scaffold_module(module_id, title, status, threat, country, industry, company_size):
    return (
        f"id: {module_id}\n"
        f"title: {title}\n"
        "version: '0.1'\n"
        f"status: {status}\n"
        f"threat: {threat}\n"
        "description: >\n"
        "  REPLACE_ME with practitioner-facing scope, intended use, limitations,\n"
        "  and what evidence is still needed.\n"
        "context:\n"
        f"  industry: {industry}\n"
        f"  country: {country}\n"
        f"  company_size: {company_size}\n"
        "artifacts:\n"
        f"  scenario: scenarios/{module_id}.yaml\n"
        f"  org_profile: org_profiles/{module_id}.yaml\n"
        f"  calibration: calibrations/{module_id}.yaml\n"
        f"  evidence: [evidence/{module_id}.yaml]\n"
        f"  extractions: [extractions/{module_id}_reviewed.yaml]\n"
        "required_parameters: [frequency.min, frequency.likely, frequency.max, impact.min, impact.likely, impact.max]\n"
        "tags:\n"
        f"  - {country.lower()}\n"
        f"  - {industry}\n"
        f"  - {company_size}\n"
        f"  - {threat}\n"
        "practitioner_notes:\n"
        "  good_for: REPLACE_ME with intended practitioner/researcher usage.\n"
        "  not_good_for: Benchmark claims until placeholders are replaced and reviewed.\n"
    )


def check(name, status, detail):
    return {"name": name, "status": status, "detail": detail}


def aggregate_status(checks):
    statuses = {item["status"] for item in checks}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "needs_review"
    return "pass"


def truncate_issues(issues, limit=4):
    detail = "; ".join(issues[:limit])
    if len(issues) > limit:
        detail += f"; {len(issues) - limit} more"
    return detail


def relative_to_root_or_cwd(path, root):
    path = Path(path)
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            return str(path)
