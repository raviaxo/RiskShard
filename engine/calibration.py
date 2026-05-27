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

    generated = {
        "metadata": {
            "name": calibration_profile.get("metadata", {}).get(
                "scenario_name",
                f"{scenario['metadata']['name']} Calibrated",
            ),
            "version": calibration_profile.get("metadata", {}).get("version", "0.1-calibrated"),
        },
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

    selected_ids = {item["evidence_id"] for item in selected}
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
            "as_of": conversion["as_of"],
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


def validate_generated_ranges(scenario):
    for group in PARAMETER_GROUPS:
        values = scenario[group]
        if values["min"] > values["likely"] or values["likely"] > values["max"]:
            raise CalibrationError(f"Generated {group} range must satisfy min <= likely <= max")


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


def write_calibrated_scenario(report, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(report["generated_scenario"], sort_keys=False))
    return output_path
