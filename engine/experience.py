from pathlib import Path

from engine.evidence import load_evidence_records, match_evidence
from engine.evidence_quality import load_source_manifest
from engine.profiles import load_org_profile, load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "sources" / "manifest.json"
DEFAULT_THREAT_LIBRARY_PATH = PROJECT_ROOT / "threat_library" / "starter_pack.yaml"
DEFAULT_CALIBRATION_DIR = PROJECT_ROOT / "calibrations"

SCENARIO_PARAMETERS = (
    "frequency.min",
    "frequency.likely",
    "frequency.max",
    "impact.min",
    "impact.likely",
    "impact.max",
)


def analyze_gaps(
    org_profile_path,
    threat,
    *,
    evidence_path=DEFAULT_EVIDENCE_DIR,
    manifest_path=DEFAULT_MANIFEST_PATH,
    calibration_dir=DEFAULT_CALIBRATION_DIR,
    calibration_path=None,
):
    org_profile = load_org_profile(org_profile_path)
    evidence_records = load_evidence_records(evidence_path)
    evidence_by_id = {record["id"]: record for record in evidence_records}
    manifest_by_id = load_source_manifest(manifest_path)
    matched = match_evidence(evidence_records, org_profile, threat)
    matches_by_parameter = {}

    for match in matched["matches"]:
        parameter = match["record"]["parameter"]
        matches_by_parameter.setdefault(parameter, []).append(match)

    if calibration_path is None:
        calibration_path = default_calibration_path(calibration_dir, matched["target_context"]["threat"])
    else:
        calibration_path = Path(calibration_path)
    calibration_profile_exists = calibration_path.exists()
    calibration_selections = (
        load_calibration_selections(calibration_path, evidence_by_id)
        if calibration_profile_exists
        else {}
    )

    direct_parameters = []
    missing_parameters = []
    assumption_parameters = []
    source_warnings = []

    for parameter in SCENARIO_PARAMETERS:
        candidates = matches_by_parameter.get(parameter, [])
        selected_record = calibration_selections.get(parameter)
        if selected_record is not None:
            selected_match = first_match_for_record(candidates, selected_record["id"])
            source_status = evidence_source_status(selected_record, manifest_by_id)
            status = "ready"
            if selected_record["evidence_type"] != "source_backed":
                status = "assumption_only"
                assumption_parameters.append(parameter)
            if source_status == "not_fetched":
                source_warnings.append(parameter)

            direct_parameters.append({
                "parameter": parameter,
                "status": status,
                "best": summarize_record(selected_record, manifest_by_id, selected_match),
                "candidate_count": len(candidates),
                "selected_by": "calibration_profile",
            })
            continue

        if not candidates:
            direct_parameters.append({
                "parameter": parameter,
                "status": "missing",
                "best": None,
                "candidate_count": 0,
                "selected_by": "evidence_match",
            })
            missing_parameters.append(parameter)
            continue

        best = candidates[0]
        record = best["record"]
        source_status = evidence_source_status(record, manifest_by_id)
        status = "ready"
        if record["evidence_type"] != "source_backed":
            status = "assumption_only"
            assumption_parameters.append(parameter)
        if source_status == "not_fetched":
            source_warnings.append(parameter)

        direct_parameters.append({
            "parameter": parameter,
                "status": status,
                "best": summarize_best_match(best, manifest_by_id),
                "candidate_count": len(candidates),
                "selected_by": "evidence_match",
            })

    context_parameters = [
        {
            "parameter": parameter,
            "best": summarize_best_match(matches[0], manifest_by_id),
            "candidate_count": len(matches),
        }
        for parameter, matches in sorted(matches_by_parameter.items())
        if parameter not in SCENARIO_PARAMETERS
    ]

    return {
        "target_context": matched["target_context"],
        "org_profile": str(org_profile_path),
        "threat": matched["target_context"]["threat"],
        "direct_parameters": direct_parameters,
        "context_parameters": context_parameters,
        "missing_parameters": missing_parameters,
        "assumption_parameters": assumption_parameters,
        "source_warnings": source_warnings,
        "calibration_profile": str(calibration_path),
        "calibration_profile_exists": calibration_profile_exists,
    }


def load_calibration_selections(calibration_path, evidence_by_id):
    profile = load_yaml_file(calibration_path)
    selections = {}

    for group, bounds in {"frequency": ("min", "likely", "max"), "impact": ("min", "likely", "max")}.items():
        group_spec = profile.get("parameters", {}).get(group, {})
        for bound in bounds:
            selector = group_spec.get(bound)
            if not selector:
                continue
            record = evidence_by_id.get(selector.get("evidence_id"))
            if record is not None:
                selections[f"{group}.{bound}"] = record

    return selections


def first_match_for_record(candidates, record_id):
    for candidate in candidates:
        if candidate["record"]["id"] == record_id:
            return candidate
    return None


def summarize_best_match(match, manifest_by_id):
    return summarize_record(match["record"], manifest_by_id, match)


def summarize_record(record, manifest_by_id, match=None):
    return {
        "id": record["id"],
        "title": record["title"],
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "score": match["score"] if match else None,
        "source_id": record.get("source_id"),
        "source_name": record["source_name"],
        "source_status": evidence_source_status(record, manifest_by_id),
        "limitations": record["limitations"],
    }


def evidence_source_status(record, manifest_by_id):
    if record["evidence_type"] != "source_backed":
        return "not_required"
    source = manifest_by_id.get(record.get("source_id"))
    if source is None:
        return "unknown"
    if source.get("status") != "fetched":
        return "not_fetched"
    return "fetched"


def default_calibration_path(calibration_dir, threat):
    return Path(calibration_dir) / f"au_finance_{threat}.yaml"


def rank_top_risks(
    org_profile_path,
    *,
    evidence_path=DEFAULT_EVIDENCE_DIR,
    manifest_path=DEFAULT_MANIFEST_PATH,
    threat_library_path=DEFAULT_THREAT_LIBRARY_PATH,
    calibration_dir=DEFAULT_CALIBRATION_DIR,
):
    library = load_yaml_file(threat_library_path)
    rows = []

    for threat in library["threats"]:
        analysis = analyze_gaps(
            org_profile_path,
            threat["id"],
            evidence_path=evidence_path,
            manifest_path=manifest_path,
            calibration_dir=calibration_dir,
        )
        covered = len(SCENARIO_PARAMETERS) - len(analysis["missing_parameters"])
        assumption_count = len(analysis["assumption_parameters"])
        context_count = len(analysis["context_parameters"])
        status = top_risk_status(analysis, covered, context_count)
        next_steps = top_risk_next_steps(analysis)

        rows.append({
            "id": threat["id"],
            "label": threat["label"],
            "library_status": threat["status"],
            "status": status,
            "direct_coverage": covered,
            "direct_total": len(SCENARIO_PARAMETERS),
            "context_evidence": context_count,
            "assumption_parameters": assumption_count,
            "missing_parameters": analysis["missing_parameters"],
            "calibration_profile_exists": analysis["calibration_profile_exists"],
            "next_steps": next_steps,
        })

    rows.sort(key=top_risk_sort_key)
    return rows


def top_risk_status(analysis, covered, context_count):
    if (
        analysis["calibration_profile_exists"]
        and covered == len(SCENARIO_PARAMETERS)
        and not analysis["assumption_parameters"]
        and not analysis["source_warnings"]
    ):
        return "calibrated"
    if analysis["calibration_profile_exists"] and covered == len(SCENARIO_PARAMETERS):
        return "calibrated_with_assumptions"
    if covered or context_count:
        return "partially_supported"
    return "missing_evidence"


def top_risk_next_steps(analysis):
    steps = []
    if analysis["missing_parameters"]:
        steps.append("add direct evidence for " + ", ".join(analysis["missing_parameters"][:3]))
    if analysis["assumption_parameters"]:
        steps.append("replace assumptions for " + ", ".join(analysis["assumption_parameters"][:3]))
    if not analysis["calibration_profile_exists"]:
        steps.append("add calibration profile")
    if analysis["source_warnings"]:
        steps.append("fix source fetch warnings")
    return steps or ["ready for calibrated run"]


def top_risk_sort_key(row):
    status_rank = {
        "calibrated": 0,
        "calibrated_with_assumptions": 1,
        "partially_supported": 2,
        "missing_evidence": 3,
    }
    return (
        status_rank[row["status"]],
        -row["direct_coverage"],
        row["assumption_parameters"],
        -row["context_evidence"],
        row["id"],
    )


def format_gap_analysis(analysis):
    lines = [
        f"Gap analysis: {analysis['threat']}",
        (
            "Context: "
            f"industry={analysis['target_context']['industry']} "
            f"country={analysis['target_context']['country']} "
            f"size={analysis['target_context']['company_size']}"
        ),
        "",
        "Scenario parameters",
    ]

    for item in analysis["direct_parameters"]:
        if item["best"] is None:
            lines.append(f"- {item['parameter']}: MISSING")
            continue
        best = item["best"]
        suffix = []
        if item["status"] == "assumption_only":
            suffix.append("assumption")
        if best["source_status"] == "not_fetched":
            suffix.append("source not fetched")
        suffix_text = f" ({', '.join(suffix)})" if suffix else ""
        lines.append(
            f"- {item['parameter']}: {best['id']} "
            f"score={best['score']} {best['evidence_type']} "
            f"confidence={best['confidence']}{suffix_text}"
        )

    if analysis["context_parameters"]:
        lines.extend(["", "Context evidence"])
        for item in analysis["context_parameters"][:6]:
            best = item["best"]
            lines.append(f"- {item['parameter']}: {best['id']} score={best['score']}")

    lines.extend(["", "Next steps"])
    for step in top_risk_next_steps(analysis):
        lines.append(f"- {step}")

    return "\n".join(lines) + "\n"


def format_top_risks(rows):
    lines = ["Top risks", ""]
    for row in rows:
        next_step = row["next_steps"][0] if row["next_steps"] else "ready"
        lines.extend([
            f"- {row['label']}: {row['status']}",
            f"  direct: {row['direct_coverage']}/{row['direct_total']}; context: {row['context_evidence']}; assumptions: {row['assumption_parameters']}",
            f"  next: {next_step}",
        ])
    return "\n".join(lines) + "\n"


def propose_calibration(
    org_profile_path,
    threat,
    *,
    evidence_path=DEFAULT_EVIDENCE_DIR,
    manifest_path=DEFAULT_MANIFEST_PATH,
    calibration_dir=DEFAULT_CALIBRATION_DIR,
):
    analysis = analyze_gaps(
        org_profile_path,
        threat,
        evidence_path=evidence_path,
        manifest_path=manifest_path,
        calibration_dir=calibration_dir,
    )
    selectors = []
    for item in analysis["direct_parameters"]:
        best = item["best"]
        selectors.append({
            "parameter": item["parameter"],
            "status": item["status"],
            "evidence_id": best["id"] if best else None,
            "evidence_type": best["evidence_type"] if best else None,
            "confidence": best["confidence"] if best else None,
            "source_status": best["source_status"] if best else None,
        })

    return {
        "threat": analysis["threat"],
        "target_context": analysis["target_context"],
        "calibration_profile_exists": analysis["calibration_profile_exists"],
        "profile_ready": (
            not analysis["missing_parameters"]
            and not analysis["assumption_parameters"]
            and not analysis["source_warnings"]
        ),
        "selectors": selectors,
        "next_steps": top_risk_next_steps(analysis),
    }


def format_calibration_proposal(proposal):
    lines = [
        f"Calibration proposal: {proposal['threat']}",
        f"Profile exists: {proposal['calibration_profile_exists']}",
        f"Ready without assumptions or source warnings: {proposal['profile_ready']}",
        "",
        "Candidate selectors",
    ]
    for item in proposal["selectors"]:
        if item["evidence_id"] is None:
            lines.append(f"- {item['parameter']}: MISSING")
            continue
        lines.append(
            f"- {item['parameter']}: {item['evidence_id']} "
            f"{item['evidence_type']} confidence={item['confidence']} source={item['source_status']}"
        )
    lines.extend(["", "Next steps"])
    for step in proposal["next_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines) + "\n"
