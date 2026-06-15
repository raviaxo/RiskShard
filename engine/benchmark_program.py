from collections import Counter
from pathlib import Path

from engine.evidence_packs import load_module_evidence_records
from engine.extractions import load_extractions
from engine.governance import build_data_feed_inventory
from engine.profiles import load_yaml_file
from engine.risk_modules import REQUIRED_PARAMETERS, load_risk_modules
from engine.taxonomy import load_taxonomies


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_PATH = PROJECT_ROOT / "benchmark_targets" / "benchmark_grade_30.yaml"
PARAMETER_GROUPS = {
    "frequency": ("min", "likely", "max"),
    "impact": ("min", "likely", "max"),
}
CONFIDENCE_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
MIN_BENCHMARK_CONFIDENCE = "medium"
MIN_SELECTED_SOURCE_COUNT = 2
MIN_COUNTRY_SPECIFIC_PARAMETERS = 3
MIN_INDUSTRY_SPECIFIC_PARAMETERS = 2


def build_benchmark_program_report(root=PROJECT_ROOT, target_path=DEFAULT_TARGET_PATH):
    root = Path(root)
    program = load_yaml_file(target_path)
    taxonomies = taxonomy_id_sets(root)
    modules = {module["id"]: module for module in load_risk_modules(root)}
    feed_inventory = build_data_feed_inventory(
        registry_path=root / "sources" / "registry.yaml",
        manifest_path=root / "sources" / "manifest.json",
        evidence_path=root / "evidence",
    )
    feeds_by_id = {feed["id"]: feed for feed in feed_inventory["feeds"]}
    targets = [
        evaluate_target(target, root, modules, feeds_by_id, taxonomies)
        for target in sorted(program["targets"], key=lambda item: item["priority"])
    ]
    status_counts = Counter(target["status"] for target in targets)
    validation_issues = validate_program(program, targets, taxonomies)

    return {
        "program": program["program"],
        "status": "pass" if not validation_issues else "fail",
        "target_count": len(targets),
        "benchmark_ready_count": status_counts.get("benchmark_ready", 0),
        "module_seeded_count": len([item for item in targets if item["module_present"]]),
        "status_counts": dict(sorted(status_counts.items())),
        "validation_issues": validation_issues,
        "targets": targets,
    }


def taxonomy_id_sets(root):
    taxonomies = load_taxonomies(root / "taxonomies")
    return {
        "countries": {item["id"] for item in taxonomies["countries"]},
        "industries": {item["id"] for item in taxonomies["industries"]},
        "company_sizes": {item["id"] for item in taxonomies["company_sizes"]},
        "threats": {item["id"] for item in taxonomies["threats"]},
    }


def validate_program(program, targets, taxonomies):
    issues = []
    expected_count = program["program"].get("target_count")
    if expected_count != len(targets):
        issues.append({
            "code": "target_count_mismatch",
            "message": f"program.target_count={expected_count}, actual={len(targets)}",
        })

    ids = [target["id"] for target in targets]
    duplicate_ids = sorted(id_ for id_, count in Counter(ids).items() if count > 1)
    for target_id in duplicate_ids:
        issues.append({"code": "duplicate_target_id", "target_id": target_id})

    priorities = [target["priority"] for target in targets]
    duplicate_priorities = sorted(priority for priority, count in Counter(priorities).items() if count > 1)
    for priority in duplicate_priorities:
        issues.append({"code": "duplicate_priority", "priority": priority})

    for target in targets:
        context = target["context"]
        for field, taxonomy_name in (
            ("country", "countries"),
            ("industry", "industries"),
            ("company_size", "company_sizes"),
            ("threat", "threats"),
        ):
            if context[field] not in taxonomies[taxonomy_name]:
                issues.append({
                    "code": "unknown_taxonomy_id",
                    "target_id": target["id"],
                    "field": field,
                    "value": context[field],
                })

    return issues


def evaluate_target(target, root, modules_by_id, feeds_by_id, taxonomies):
    module_id = target.get("module_id") or target["id"]
    module = modules_by_id.get(module_id)
    criteria = {}
    selected_parameters = []

    criteria["valid_taxonomy"] = valid_target_taxonomy(target, taxonomies)
    criteria["module_exists"] = module is not None
    if module is None:
        return target_summary(
            target,
            module_id,
            module_present=False,
            status="missing_module",
            criteria=criteria,
            selected_parameters=[],
            next_actions=["create governed risk module artifacts"],
        )

    context_matches = module_context_matches(target, module)
    selected_parameters = selected_parameter_rows(module, root, feeds_by_id)
    complete_count = len([item for item in selected_parameters if item["record_found"]])
    source_backed_count = len([item for item in selected_parameters if item["evidence_type"] == "source_backed"])
    confidence_count = len([
        item for item in selected_parameters
        if CONFIDENCE_RANK.get(item["confidence"], 0) >= CONFIDENCE_RANK[MIN_BENCHMARK_CONFIDENCE]
    ])
    current_source_count = len([
        item for item in selected_parameters
        if item["record_found"] and item["source_renewal_status"] == "current"
    ])
    extracted_count = len([
        item for item in selected_parameters
        if item["record_found"] and item["mapped_to_reviewed_extraction"]
    ])
    selected_source_ids = {
        item["source_id"]
        for item in selected_parameters
        if item["record_found"] and item["source_id"]
    }
    country_specific_count = len([
        item for item in selected_parameters
        if target["context"]["country"] in item["applicability"].get("countries", [])
    ])
    industry_specific_count = len([
        item for item in selected_parameters
        if target["context"]["industry"] in item["applicability"].get("industries", [])
    ])

    criteria.update({
        "module_context_matches_target": context_matches,
        "all_six_parameters_selected": complete_count == len(REQUIRED_PARAMETERS),
        "all_selected_parameters_source_backed": source_backed_count == len(REQUIRED_PARAMETERS),
        "selected_confidence_medium_or_high": confidence_count == len(REQUIRED_PARAMETERS),
        "selected_sources_current": current_source_count == len(REQUIRED_PARAMETERS),
        "selected_evidence_mapped_to_extractions": extracted_count == len(REQUIRED_PARAMETERS),
        "at_least_two_selected_sources": len(selected_source_ids) >= MIN_SELECTED_SOURCE_COUNT,
        "country_relevance_minimum_met": country_specific_count >= MIN_COUNTRY_SPECIFIC_PARAMETERS,
        "industry_relevance_minimum_met": industry_specific_count >= MIN_INDUSTRY_SPECIFIC_PARAMETERS,
    })
    status = "benchmark_ready" if all(criteria.values()) else "needs_evidence"

    return target_summary(
        target,
        module_id,
        module_present=True,
        status=status,
        criteria=criteria,
        selected_parameters=selected_parameters,
        next_actions=target_next_actions(criteria, selected_parameters, target["context"]),
        metrics={
            "selected_parameters": complete_count,
            "source_backed_parameters": source_backed_count,
            "confidence_medium_or_high_parameters": confidence_count,
            "current_source_parameters": current_source_count,
            "extracted_parameters": extracted_count,
            "selected_source_count": len(selected_source_ids),
            "country_specific_parameters": country_specific_count,
            "industry_specific_parameters": industry_specific_count,
        },
    )


def valid_target_taxonomy(target, taxonomies):
    context = target["context"]
    return (
        context["country"] in taxonomies["countries"]
        and context["industry"] in taxonomies["industries"]
        and context["company_size"] in taxonomies["company_sizes"]
        and context["threat"] in taxonomies["threats"]
    )


def module_context_matches(target, module):
    context = target["context"]
    module_context = module["context"]
    return (
        module["threat"] == context["threat"]
        and module_context["country"] == context["country"]
        and module_context["industry"] == context["industry"]
        and module_context["company_size"] == context["company_size"]
    )


def selected_parameter_rows(module, root, feeds_by_id):
    evidence_records = load_module_evidence_records(module, root)
    records_by_id = {record["id"]: record for record in evidence_records}
    calibration = load_yaml_file(root / module["artifacts"]["calibration"])
    extracted_evidence_ids = module_extracted_evidence_ids(module, root)
    rows = []

    for group, bounds in PARAMETER_GROUPS.items():
        group_spec = calibration.get("parameters", {}).get(group, {})
        for bound in bounds:
            parameter = f"{group}.{bound}"
            selector = group_spec.get(bound) or {}
            evidence_id = selector.get("evidence_id")
            record = records_by_id.get(evidence_id)
            feed = feeds_by_id.get(record.get("source_id")) if record else None
            rows.append(selected_parameter_row(parameter, evidence_id, record, feed, extracted_evidence_ids))

    return rows


def module_extracted_evidence_ids(module, root):
    evidence_ids = set()
    for extraction_path in module["artifacts"].get("extractions", []):
        for extraction in load_extractions(root / extraction_path):
            evidence_ids.update(extraction["evidence_record_ids"])
    return evidence_ids


def selected_parameter_row(parameter, evidence_id, record, feed, extracted_evidence_ids):
    if record is None:
        return {
            "parameter": parameter,
            "evidence_id": evidence_id,
            "record_found": False,
            "evidence_type": None,
            "confidence": None,
            "source_id": None,
            "source_renewal_status": None,
            "mapped_to_reviewed_extraction": False,
            "applicability": {"countries": [], "industries": [], "company_size_bands": []},
        }

    return {
        "parameter": parameter,
        "evidence_id": evidence_id,
        "record_found": True,
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "source_id": record.get("source_id"),
        "source_renewal_status": feed["renewal_status"] if feed else "unknown",
        "source_trust_tier": feed["trust_tier"] if feed else "unknown",
        "mapped_to_reviewed_extraction": record["id"] in extracted_evidence_ids,
        "applicability": record.get("applicability", {}),
    }


def target_next_actions(criteria, selected_parameters, context):
    actions = []
    if not criteria.get("module_context_matches_target", True):
        actions.append("align module threat and context with benchmark target")
    if not criteria.get("all_six_parameters_selected", True):
        missing = [item["parameter"] for item in selected_parameters if not item["record_found"]]
        actions.append("select evidence for " + ", ".join(missing[:3]))
    if not criteria.get("all_selected_parameters_source_backed", True):
        weak = [item["parameter"] for item in selected_parameters if item["evidence_type"] != "source_backed"]
        actions.append("replace non-source-backed selectors for " + ", ".join(weak[:3]))
    if not criteria.get("selected_confidence_medium_or_high", True):
        low = [
            item["parameter"]
            for item in selected_parameters
            if CONFIDENCE_RANK.get(item["confidence"], 0) < CONFIDENCE_RANK[MIN_BENCHMARK_CONFIDENCE]
        ]
        actions.append("replace or strengthen low-confidence selectors for " + ", ".join(low[:3]))
    if not criteria.get("selected_sources_current", True):
        stale = [item["parameter"] for item in selected_parameters if item["source_renewal_status"] != "current"]
        actions.append("refresh or gather sources for " + ", ".join(stale[:3]))
    if not criteria.get("selected_evidence_mapped_to_extractions", True):
        unmapped = [
            item["parameter"]
            for item in selected_parameters
            if item["record_found"] and not item["mapped_to_reviewed_extraction"]
        ]
        actions.append("map selected evidence to reviewed extractions for " + ", ".join(unmapped[:3]))
    if not criteria.get("at_least_two_selected_sources", True):
        actions.append("add at least one independent selected source")
    if not criteria.get("country_relevance_minimum_met", True):
        actions.append(f"add more {context['country']}-specific selected evidence")
    if not criteria.get("industry_relevance_minimum_met", True):
        actions.append(f"add more {context['industry']}-specific selected evidence")
    return actions or ["ready for human benchmark review"]


def target_summary(
    target,
    module_id,
    *,
    module_present,
    status,
    criteria,
    selected_parameters,
    next_actions,
    metrics=None,
):
    return {
        "priority": target["priority"],
        "id": target["id"],
        "module_id": module_id,
        "wave": target["wave"],
        "context": target["context"],
        "module_present": module_present,
        "status": status,
        "criteria": criteria,
        "metrics": metrics or {},
        "selected_parameters": selected_parameters,
        "next_actions": next_actions,
        "rationale": target.get("rationale", ""),
    }


def format_benchmark_program_report(report, *, target_id=None):
    lines = [
        f"{report['program']['title']}",
        f"Status: {report['status']}",
        (
            f"Targets: {report['target_count']}; "
            f"modules seeded: {report['module_seeded_count']}; "
            f"benchmark-ready: {report['benchmark_ready_count']}"
        ),
        "Statuses: " + format_counts(report["status_counts"]),
        "",
    ]

    if report["validation_issues"]:
        lines.append("Validation issues")
        for issue in report["validation_issues"]:
            lines.append(f"- {issue['code']}: {issue}")
        lines.append("")

    targets = report["targets"]
    if target_id:
        targets = [target for target in targets if target["id"] == target_id or target["module_id"] == target_id]

    for target in targets:
        metrics = target["metrics"]
        if target["module_present"]:
            metric_text = (
                f"selected={metrics['selected_parameters']}/6; "
                f"source_backed={metrics['source_backed_parameters']}/6; "
                f"confidence>=medium={metrics['confidence_medium_or_high_parameters']}/6; "
                f"current_sources={metrics['current_source_parameters']}/6"
            )
        else:
            metric_text = "module not created"
        lines.extend([
            f"- {target['priority']:02d}. {target['id']}: {target['status']}",
            f"  context: {target['context']['country']}/{target['context']['industry']}/{target['context']['company_size']}/{target['context']['threat']}",
            f"  metrics: {metric_text}",
            f"  next: {target['next_actions'][0]}",
        ])

    if target_id and not targets:
        lines.append(f"No benchmark target found for: {target_id}")

    return "\n".join(lines) + "\n"


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) or "none"
