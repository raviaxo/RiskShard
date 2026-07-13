from pathlib import Path

from engine.evidence import load_evidence_records, match_evidence
from engine.evidence_packs import source_ids_for_records
from engine.experience import load_calibration_selections
from engine.governance import build_data_feed_inventory
from engine.profiles import load_org_profile, load_yaml_file
from engine.risk_modules import REQUIRED_PARAMETERS, find_risk_module


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}


def propose_module_calibration(module_id, root=PROJECT_ROOT, org_profile_path=None):
    root = Path(root)
    module = find_risk_module(module_id, root)
    if module is None:
        raise ValueError(f"Unknown risk module: {module_id}")

    org_profile_path = Path(org_profile_path or root / module["artifacts"]["org_profile"])
    org_profile = load_org_profile(org_profile_path)
    evidence_records = load_evidence_records(root / "evidence")
    evidence_by_id = {record["id"]: record for record in evidence_records}
    feed_inventory = build_data_feed_inventory(
        registry_path=root / "sources" / "registry.yaml",
        manifest_path=root / "sources" / "manifest.json",
        evidence_path=root / "evidence",
    )
    feeds_by_id = {feed["id"]: feed for feed in feed_inventory["feeds"]}
    matched = match_evidence(
        evidence_records,
        org_profile,
        module["threat"],
        parameters=module.get("required_parameters") or REQUIRED_PARAMETERS,
    )
    module_evidence_files = {
        str(root / evidence_path)
        for evidence_path in module["artifacts"].get("evidence", [])
    }
    calibration_path = root / module["artifacts"]["calibration"]
    calibration_profile = load_yaml_file(calibration_path) if calibration_path.exists() else {}
    target_currency = calibration_profile.get("target_currency")
    current_selections = (
        load_calibration_selections(calibration_path, evidence_by_id)
        if calibration_path.exists()
        else {}
    )

    selectors = []
    for parameter in module.get("required_parameters") or REQUIRED_PARAMETERS:
        candidates = [
            candidate
            for candidate in matched["matches"]
            if candidate["record"]["parameter"] == parameter
            and candidate["record"].get("_source_file") in module_evidence_files
        ]
        candidates = sorted(
            candidates,
            key=lambda candidate: candidate_sort_key(candidate, module_evidence_files),
        )
        best = candidates[0] if candidates else None
        current = current_selections.get(parameter)
        selectors.append({
            "parameter": parameter,
            "status": selector_status(best, current),
            "current": summarize_record(current, feeds_by_id) if current else None,
            "best": summarize_candidate(best, feeds_by_id) if best else None,
            "candidates": [
                summarize_candidate(candidate, feeds_by_id)
                for candidate in candidates[:3]
            ],
            "draft_selector": draft_selector(parameter, best, target_currency),
        })

    return {
        "module_id": module["id"],
        "module_title": module["title"],
        "threat": module["threat"],
        "target_context": matched["target_context"],
        "calibration_profile": module["artifacts"]["calibration"],
        "calibration_profile_exists": calibration_path.exists(),
        "ready_without_assumptions": ready_without_assumptions(selectors),
        "selectors": selectors,
        "next_steps": proposal_next_steps(selectors),
    }


def selector_status(best, current):
    if best is None and current is None:
        return "missing"
    if current is None:
        if best["record"]["evidence_type"] == "source_backed":
            return "candidate_ready"
        return "candidate_is_assumption"
    if current["evidence_type"] != "source_backed":
        return "selected_assumption"
    if best and current["id"] != best["record"]["id"]:
        return "selected_not_best"
    return "selected_source_backed"


def candidate_sort_key(candidate, module_evidence_files=None):
    module_evidence_files = module_evidence_files or set()
    record = candidate["record"]
    return (
        record["evidence_type"] != "source_backed",
        record.get("_source_file") not in module_evidence_files,
        -candidate["score"],
        -exact_match(candidate, "country"),
        -exact_match(candidate, "threat"),
        -exact_match(candidate, "industry"),
        -exact_match(candidate, "company_size"),
        -CONFIDENCE_RANK[record["confidence"]],
        record["id"],
    )


def exact_match(candidate, dimension):
    return 1 if candidate["applicability"][dimension]["match"] == "exact" else 0


def summarize_candidate(candidate, feeds_by_id):
    record = candidate["record"]
    summary = summarize_record(record, feeds_by_id)
    summary.update({
        "score": candidate["score"],
        "applicability": candidate["applicability"],
    })
    return summary


def summarize_record(record, feeds_by_id):
    source_ids = sorted(source_ids_for_records([record]))
    sources = [feeds_by_id.get(source_id) for source_id in source_ids]
    renewal_statuses = sorted({
        source["renewal_status"]
        for source in sources
        if source
    })
    trust_tiers = sorted({
        source["trust_tier"]
        for source in sources
        if source
    })
    return {
        "id": record["id"],
        "title": record["title"],
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "value": record["value"],
        "unit": record["unit"],
        "currency": record.get("currency"),
        "source_ids": source_ids,
        "source_name": record["source_name"],
        "source_renewal_statuses": renewal_statuses or ["not_required"],
        "trust_tiers": trust_tiers or ["not_required"],
        "limitations": record["limitations"],
    }


def draft_selector(parameter, best, target_currency=None):
    if best is None:
        return None
    group, bound = parameter.split(".")
    record = best["record"]
    selector = {
        "group": group,
        "bound": bound,
        "evidence_id": record["id"],
        "transform": "direct",
        "rationale": "Proposed from highest-scoring evidence match for this module context.",
    }
    if (
        record["unit"] == "currency"
        and target_currency
        and record.get("currency")
        and record.get("currency") != target_currency
    ):
        selector["transform"] = "currency_convert"
        selector["target_currency"] = target_currency
    return selector


def ready_without_assumptions(selectors):
    return all(
        item["best"]
        and item["best"]["evidence_type"] == "source_backed"
        and item["status"] in {"selected_source_backed", "candidate_ready", "selected_not_best"}
        for item in selectors
    )


def proposal_next_steps(selectors):
    steps = []
    missing = [item["parameter"] for item in selectors if item["status"] == "missing"]
    assumptions = [
        item["parameter"]
        for item in selectors
        if item["status"] in {"selected_assumption", "candidate_is_assumption"}
    ]
    not_best = [item["parameter"] for item in selectors if item["status"] == "selected_not_best"]

    if missing:
        steps.append("add source-backed evidence for " + ", ".join(missing[:3]))
    if assumptions:
        steps.append("replace assumption selectors for " + ", ".join(assumptions[:3]))
    if not_best:
        steps.append("review selected-vs-best candidates for " + ", ".join(not_best[:3]))
    return steps or ["profile selectors align with best source-backed candidates"]


def format_module_calibration_proposal(proposal):
    context = proposal["target_context"]
    lines = [
        f"Module calibration proposal: {proposal['module_id']}",
        f"Title: {proposal['module_title']}",
        f"Threat: {proposal['threat']}",
        (
            "Context: "
            f"industry={context['industry']} country={context['country']} "
            f"size={context['company_size']}"
        ),
        f"Profile: {proposal['calibration_profile']} exists={proposal['calibration_profile_exists']}",
        f"Ready without assumptions: {proposal['ready_without_assumptions']}",
        "",
        "Selectors",
    ]
    for item in proposal["selectors"]:
        best = item["best"]
        current = item["current"]
        if best is None:
            lines.append(f"- {item['parameter']}: MISSING")
            continue
        current_text = current["id"] if current else "none"
        lines.append(
            f"- {item['parameter']}: {item['status']} "
            f"current={current_text} best={best['id']} "
            f"{best['evidence_type']} confidence={best['confidence']} score={best['score']}"
        )
        if best["source_renewal_statuses"]:
            lines.append(
                "  source: "
                f"{', '.join(best['source_ids']) or 'none'} "
                f"renewal={', '.join(best['source_renewal_statuses'])} "
                f"trust={', '.join(best['trust_tiers'])}"
            )
        selector = item["draft_selector"]
        if selector:
            lines.append(
                f"  draft: {selector['group']}.{selector['bound']} -> "
                f"{selector['evidence_id']} ({selector['transform']})"
            )

    lines.extend(["", "Next steps"])
    for step in proposal["next_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines) + "\n"
