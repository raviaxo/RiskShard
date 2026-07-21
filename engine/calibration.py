import json
from datetime import datetime
from pathlib import Path

import yaml

from engine.currency import convert_currency, load_fx_rates
from engine.evidence import load_evidence_records, match_evidence
from engine.evidence_quality import load_source_manifest, validate_evidence_quality
from engine.fair_calc import load_and_validate
from engine.profiles import load_org_profile, load_yaml_file
from engine.taxonomy import normalize_context


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "sources" / "manifest.json"
DEFAULT_FX_RATES_PATH = PROJECT_ROOT / "calibrations" / "fx_rates.yaml"


PARAMETER_GROUPS = {
    "frequency": ("min", "likely", "max"),
    "impact": ("min", "likely", "max"),
}


class CalibrationError(ValueError):
    pass


def load_calibration_profile(path):
    profile = load_yaml_file(path)
    if "parameters" not in profile:
        raise CalibrationError("Calibration profile must contain parameters.")
    return profile


def run_calibration(
    scenario_path,
    org_profile_path,
    evidence_path,
    calibration_path,
    *,
    threat,
    manifest_path=DEFAULT_MANIFEST_PATH,
    fx_rates_path=DEFAULT_FX_RATES_PATH,
):
    scenario = load_and_validate(scenario_path)
    org_profile = load_org_profile(org_profile_path)
    evidence_records = load_evidence_records(evidence_path)
    evidence_by_id = {record["id"]: record for record in evidence_records}
    calibration_profile = load_calibration_profile(calibration_path)
    manifest_by_id = load_source_manifest(manifest_path)
    fx_rates = load_fx_rates(fx_rates_path)
    quality_issues = validate_evidence_quality(evidence_path, manifest_path)
    target_context = normalize_context(org_profile, threat)
    matched = match_evidence(evidence_records, org_profile, threat)
    base_metadata = dict(scenario["metadata"])
    profile_metadata = calibration_profile.get("metadata", {})
    generated_metadata = {
        **base_metadata,
        "name": profile_metadata.get(
            "scenario_name",
            f"{base_metadata['name']} Calibrated",
        ),
        "version": profile_metadata.get("version", "0.1-calibrated"),
    }
    if calibration_profile.get("target_currency"):
        generated_metadata["currency"] = calibration_profile["target_currency"]

    generated = {
        "metadata": generated_metadata,
        "frequency": {},
        "impact": {},
    }
    selected = []
    warnings = []
    assumptions = []

    for group, bounds in PARAMETER_GROUPS.items():
        group_spec = calibration_profile["parameters"].get(group, {})
        for bound in bounds:
            selector = group_spec.get(bound)
            if selector is None:
                raise CalibrationError(f"Missing calibration selector for {group}.{bound}")

            selected_record, normalized, new_warnings, new_assumptions = calibrate_bound(
                group,
                bound,
                selector,
                evidence_by_id,
                manifest_by_id,
                fx_rates,
                calibration_profile,
            )
            generated[group][bound] = normalized["value"]
            selected.append(selected_record)
            warnings.extend(new_warnings)
            assumptions.extend(new_assumptions)

    validate_generated_ranges(generated)

    # ADR-0001: optionally compose conditional loss stages from the profile. Each
    # stage's conditional_probability and impact bounds resolve through the same
    # calibrate_bound path as frequency/impact (currency handling keys off the
    # evidence unit, so a descriptive group label is safe).
    generated_stages = []
    for stage_spec in calibration_profile.get("loss_stages", []) or []:
        loss_mode = stage_spec["loss_mode"]
        stage = {"loss_mode": loss_mode, "conditional_probability": {}, "impact": {}}
        for field in ("conditional_probability", "impact"):
            field_spec = stage_spec.get(field, {})
            for bound in ("min", "likely", "max"):
                selector = field_spec.get(bound)
                if selector is None:
                    raise CalibrationError(
                        f"Missing calibration selector for loss_stage {loss_mode}.{field}.{bound}"
                    )
                selected_record, normalized, new_warnings, new_assumptions = calibrate_bound(
                    f"loss_stage.{loss_mode}.{field}",
                    bound,
                    selector,
                    evidence_by_id,
                    manifest_by_id,
                    fx_rates,
                    calibration_profile,
                )
                stage[field][bound] = normalized["value"]
                selected.append(selected_record)
                warnings.extend(new_warnings)
                assumptions.extend(new_assumptions)
        generated_stages.append(stage)
    if generated_stages:
        generated["loss_stages"] = generated_stages
        validate_generated_loss_stages(generated)

    selected_ids = {item["evidence_id"] for item in selected}
    annotate_selected_evidence(selected, matched)
    excluded = [
        summarize_excluded(match["record"], match["score"])
        for match in matched["matches"]
        if match["record"]["id"] not in selected_ids
    ]

    return {
        "report_type": "scenario_calibration",
        "generated_at": datetime.now().isoformat(),
        "calibration_profile": calibration_profile.get("metadata", {}),
        "target_context": target_context,
        "base_scenario": {
            "metadata": scenario["metadata"],
            "frequency": scenario["frequency"],
            "impact": scenario["impact"],
        },
        "generated_scenario": generated,
        "selected_evidence": selected,
        "excluded_evidence": excluded,
        "assumptions": assumptions,
        "quality_issues": quality_issues,
        "warnings": warnings,
    }


def calibrate_bound(group, bound, selector, evidence_by_id, manifest_by_id, fx_rates, profile):
    evidence_id = selector["evidence_id"]
    record = evidence_by_id.get(evidence_id)
    if record is None:
        raise CalibrationError(f"Unknown evidence_id in calibration profile: {evidence_id}")

    value = record["value"]
    currency = record.get("currency")
    normalized_currency = currency
    warnings = []
    assumptions = []

    transform = selector.get("transform", "direct")
    if transform == "currency_convert":
        target_currency = selector.get("target_currency") or profile.get("target_currency")
        conversion = convert_currency(value, currency, target_currency, fx_rates)
        value = conversion["value"]
        normalized_currency = conversion["to_currency"]
        assumptions.append({
            "name": f"Currency conversion for {group}.{bound}",
            "evidence_id": evidence_id,
            "from_currency": conversion["from_currency"],
            "to_currency": conversion["to_currency"],
            "rate": conversion["rate"],
            "rate_id": conversion["rate_id"],
            "inverted_from_rate_id": conversion.get("inverted_from_rate_id"),
            "as_of": conversion["as_of"],
            "source_name": conversion["source_name"],
            "source_type": conversion["source_type"],
            "source_url": conversion.get("source_url"),
            "retrieved_at": conversion.get("retrieved_at"),
            "citation_detail": conversion.get("citation_detail"),
            "evidence_type": conversion["evidence_type"],
            "notes": conversion["notes"],
        })
    elif transform != "direct":
        raise CalibrationError(f"Unsupported calibration transform: {transform}")

    target_currency = selector.get("target_currency") or profile.get("target_currency")
    if record["unit"] == "currency" and target_currency and normalized_currency != target_currency:
        warnings.append({
            "code": "currency_mismatch",
            "parameter": f"{group}.{bound}",
            "evidence_id": evidence_id,
            "message": f"Evidence is {normalized_currency}, target scenario currency is {target_currency}.",
        })

    if "round_to" in selector:
        value = round_to(value, selector["round_to"])

    if record["evidence_type"] != "source_backed":
        warnings.append({
            "code": "parameter_from_non_source_backed_evidence",
            "parameter": f"{group}.{bound}",
            "evidence_id": evidence_id,
            "evidence_type": record["evidence_type"],
            "message": "Scenario parameter uses estimated or synthetic evidence.",
        })

    source = manifest_by_id.get(record.get("source_id"))
    if record["evidence_type"] == "source_backed" and source and source["status"] != "fetched":
        warnings.append({
            "code": "source_not_fetched",
            "parameter": f"{group}.{bound}",
            "evidence_id": evidence_id,
            "source_id": record.get("source_id"),
            "message": "Source-backed evidence references a source that was not fetched in the latest manifest.",
        })

    return {
        "parameter": f"{group}.{bound}",
        "evidence_id": evidence_id,
        "title": record["title"],
        "source_id": record.get("source_id"),
        "source_name": record["source_name"],
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "source_value": record["value"],
        "source_unit": record["unit"],
        "source_currency": record.get("currency"),
        "normalized_value": value,
        "normalized_currency": normalized_currency,
        "rationale": selector.get("rationale", ""),
        "limitations": record["limitations"],
        "citation_detail": record.get("citation_detail"),
    }, {"value": value}, warnings, assumptions


def annotate_selected_evidence(selected, match_result):
    matches = match_result["matches"]
    match_by_id = {match["record"]["id"]: match for match in matches}

    for item in selected:
        match = match_by_id.get(item["evidence_id"])
        if not match:
            item["selection"] = {
                "match_score": None,
                "best_available_for_parameter": False,
                "rationale": "Selected by calibration profile; record did not match target context.",
                "higher_scored_alternatives": [],
            }
            continue

        parameter = item["parameter"]
        best = match_result["best_by_parameter"].get(parameter)
        higher_scored_alternatives = [
            summarize_candidate(candidate)
            for candidate in matches
            if candidate["record"]["parameter"] == parameter
            and candidate["record"]["id"] != item["evidence_id"]
            and candidate["score"] > match["score"]
        ]

        item["selection"] = {
            "match_score": match["score"],
            "applicability": match["applicability"],
            "confidence_score": match["confidence_score"],
            "evidence_score": match["evidence_score"],
            "best_available_for_parameter": (
                best is not None and best["record"]["id"] == item["evidence_id"]
            ),
            "rationale": "Selected explicitly by calibration profile.",
            "higher_scored_alternatives": higher_scored_alternatives[:3],
        }


def summarize_candidate(match):
    record = match["record"]
    return {
        "id": record["id"],
        "title": record["title"],
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "score": match["score"],
        "source_id": record.get("source_id"),
        "source_name": record["source_name"],
    }


def validate_generated_ranges(scenario):
    for group in PARAMETER_GROUPS:
        values = scenario[group]
        if values["min"] > values["likely"] or values["likely"] > values["max"]:
            raise CalibrationError(f"Generated {group} range must satisfy min <= likely <= max")


def validate_generated_loss_stages(scenario):
    # ADR-0001: loss stages are not covered by validate_generated_ranges (which
    # runs before stages are composed and only iterates frequency/impact). Without
    # this an inverted stage range would pass silently and beta_pert would collapse
    # the stage to a constant equal to its min - the same mistake that raises for a
    # frequency/impact bound.
    for stage in scenario.get("loss_stages", []):
        mode = stage.get("loss_mode", "<unnamed>")
        for field in ("conditional_probability", "impact"):
            values = stage[field]
            if values["min"] > values["likely"] or values["likely"] > values["max"]:
                raise CalibrationError(
                    f"Generated loss_stage {mode}.{field} range must satisfy min <= likely <= max"
                )


def summarize_excluded(record, score):
    return {
        "id": record["id"],
        "parameter": record["parameter"],
        "title": record["title"],
        "source_id": record.get("source_id"),
        "evidence_type": record["evidence_type"],
        "confidence": record["confidence"],
        "value": record["value"],
        "unit": record["unit"],
        "currency": record.get("currency"),
        "score": score,
        "reason": "Applicable evidence, but not selected by this calibration profile.",
    }


def round_to(value, step):
    if step <= 0:
        raise CalibrationError("round_to must be greater than zero")
    return round(value / step) * step


def write_calibration_report(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return output_path


def write_calibration_markdown_report(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_calibration_markdown(report))
    return output_path


def format_calibration_markdown(report):
    generated = report["generated_scenario"]
    base = report["base_scenario"]
    stage_rows = []
    for stage in generated.get("loss_stages", []):
        mode = stage["loss_mode"]
        stage_rows.append(
            format_range_row(f"loss_stage[{mode}].conditional_probability", stage["conditional_probability"])
        )
        stage_rows.append(
            format_range_row(f"loss_stage[{mode}].impact", stage["impact"])
        )
    lines = [
        f"# Calibration Report: {generated['metadata']['name']}",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Report type: {report['report_type']}",
        f"- Target context: {format_context(report['target_context'])}",
        "",
        "## Bottom Line",
        "",
        bottom_line_summary(report),
        "",
        "## Confidence",
        "",
        confidence_summary(report),
        "",
        "## What Changed From Base Scenario",
        "",
        "| Parameter | Base min | Base likely | Base max | Calibrated min | Calibrated likely | Calibrated max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        format_change_row("frequency", base["frequency"], generated["frequency"]),
        format_change_row("impact", base["impact"], generated["impact"]),
        "",
        "## Limitations Summary",
        "",
        *limitations_summary(report),
        "",
        "## Generated Scenario",
        "",
        "| Parameter | Min | Likely | Max |",
        "| --- | ---: | ---: | ---: |",
        format_range_row("frequency", generated["frequency"]),
        format_range_row("impact", generated["impact"]),
        *stage_rows,
        "",
        "## Selected Evidence",
        "",
    ]

    for item in report["selected_evidence"]:
        lines.extend([
            f"### {item['parameter']}: {item['title']}",
            "",
            f"- Evidence ID: {item['evidence_id']}",
            f"- Evidence type: {item['evidence_type']}",
            f"- Confidence: {item['confidence']}",
            f"- Source: {item['source_name']}",
            f"- Match score: {item.get('selection', {}).get('match_score', 'n/a')}",
            f"- Best available for parameter: {item.get('selection', {}).get('best_available_for_parameter', False)}",
            f"- Source value: {format_value(item['source_value'])} {item['source_unit']}",
            f"- Normalized value: {format_value(item['normalized_value'])}",
            f"- Citation detail: {item.get('citation_detail') or 'n/a'}",
            f"- Limitations: {item['limitations']}",
            "",
        ])
        alternatives = item.get("selection", {}).get("higher_scored_alternatives", [])
        if alternatives:
            lines.extend([
                "Higher-scored alternatives:",
                "",
                "| Evidence ID | Evidence type | Confidence | Score | Source |",
                "| --- | --- | --- | ---: | --- |",
            ])
            for alternative in alternatives:
                lines.append(
                    "| "
                    f"{alternative['id']} | {alternative['evidence_type']} | "
                    f"{alternative['confidence']} | {alternative['score']} | "
                    f"{alternative['source_name']} |"
                )
            lines.append("")

    lines.extend([
        "## Excluded Evidence",
        "",
    ])
    if report["excluded_evidence"]:
        lines.extend([
            "| Evidence ID | Parameter | Evidence type | Score | Reason |",
            "| --- | --- | --- | ---: | --- |",
        ])
        for item in report["excluded_evidence"]:
            lines.append(
                "| "
                f"{item['id']} | {item['parameter']} | {item['evidence_type']} | "
                f"{item['score']} | {item['reason']} |"
            )
        lines.append("")
    else:
        lines.extend(["No applicable evidence was excluded.", ""])

    lines.extend([
        "## Assumptions",
        "",
    ])
    if report["assumptions"]:
        for item in report["assumptions"]:
            lines.extend([
                f"### {item['name']}",
                "",
                f"- Evidence ID: {item['evidence_id']}",
                f"- Evidence type: {item['evidence_type']}",
                f"- Rate ID: {item['rate_id']}",
                f"- Inverted from rate ID: {item.get('inverted_from_rate_id') or 'n/a'}",
                f"- Rate: {item['rate']}",
                f"- As of: {item['as_of']}",
                f"- Retrieved at: {item.get('retrieved_at') or 'n/a'}",
                f"- Source: {item.get('source_name') or 'n/a'}",
                f"- Source URL: {item.get('source_url') or 'n/a'}",
                f"- Citation detail: {item.get('citation_detail') or 'n/a'}",
                f"- Notes: {item.get('notes') or 'n/a'}",
                "",
            ])
    else:
        lines.extend(["No normalization assumptions were recorded.", ""])

    lines.extend([
        "## Warnings",
        "",
    ])
    if report["warnings"]:
        for item in report["warnings"]:
            lines.append(f"- {item['code']}: {item['message']}")
        lines.append("")
    else:
        lines.extend(["No warnings.", ""])

    lines.extend([
        "## Quality Issues",
        "",
    ])
    if report["quality_issues"]:
        for item in report["quality_issues"]:
            lines.append(f"- {item['severity']} {item['code']}: {item['message']}")
        lines.append("")
    else:
        lines.extend(["No evidence quality issues.", ""])

    return "\n".join(lines).rstrip() + "\n"


def bottom_line_summary(report):
    generated = report["generated_scenario"]
    warnings = len(report["warnings"])
    issues = len(report["quality_issues"])
    return (
        "The calibrated draft sets likely annual frequency to "
        f"{format_value(generated['frequency']['likely'])} and likely single-event impact to "
        f"{format_value(generated['impact']['likely'])}. "
        f"It should be reviewed with {warnings} warning(s) and {issues} quality issue(s) visible."
    )


def confidence_summary(report):
    selected = report["selected_evidence"]
    source_backed = sum(1 for item in selected if item["evidence_type"] == "source_backed")
    estimated = len(selected) - source_backed
    low_confidence = sum(1 for item in selected if item["confidence"] == "low")
    if estimated or low_confidence or report["quality_issues"]:
        level = "low-to-medium"
    else:
        level = "medium"
    return (
        f"Overall confidence: {level}. "
        f"{source_backed} of {len(selected)} selected parameters are source-backed; "
        f"{estimated} use estimated or synthetic evidence; "
        f"{low_confidence} selected records are low confidence."
    )


def limitations_summary(report):
    lines = []
    estimated = [
        item["parameter"]
        for item in report["selected_evidence"]
        if item["evidence_type"] != "source_backed"
    ]
    if estimated:
        lines.append("- Estimated parameters: " + ", ".join(estimated))
    if report["warnings"]:
        warning_codes = sorted({item["code"] for item in report["warnings"]})
        lines.append("- Warning codes: " + ", ".join(warning_codes))
    if report["quality_issues"]:
        issue_codes = sorted({item["code"] for item in report["quality_issues"]})
        lines.append("- Quality issue codes: " + ", ".join(issue_codes))
    if not lines:
        lines.append("- No material limitations were recorded by the calibration workflow.")
    return lines


def format_context(context):
    return ", ".join(f"{key}={value}" for key, value in sorted(context.items()))


def format_range_row(name, values):
    return f"| {name} | {format_value(values['min'])} | {format_value(values['likely'])} | {format_value(values['max'])} |"


def format_change_row(name, base, generated):
    return (
        f"| {name} | "
        f"{format_value(base['min'])} | {format_value(base['likely'])} | {format_value(base['max'])} | "
        f"{format_value(generated['min'])} | {format_value(generated['likely'])} | {format_value(generated['max'])} |"
    )


def format_value(value):
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def write_calibrated_scenario(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(report["generated_scenario"], sort_keys=False))
    return output_path
