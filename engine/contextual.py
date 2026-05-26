import json
import random
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from engine.analysis.comparator import compare_runs
from engine.controls.engine import apply_controls
from engine.controls.loader import load_control_profile, load_controls
from engine.evidence import load_evidence_records, match_evidence, summarize_match
from engine.fair_calc import (
    RESULTS_DIR,
    compute_stats,
    load_and_validate,
    run_simulation,
)
from engine.profiles import load_org_profile, load_provenance


RISK_LEVEL_MULTIPLIERS = {
    "low": 0.85,
    "moderate": 1.0,
    "high": 1.15,
    "very_high": 1.3,
}

CONFIDENCE_ORDER = {"low": 1, "medium": 2, "high": 3}


def scale_range(values, multiplier):
    return {
        "min": values["min"] * multiplier,
        "likely": values["likely"] * multiplier,
        "max": values["max"] * multiplier,
    }


def contextualize_scenario(scenario, org_profile):
    contextualized = deepcopy(scenario)

    frequency_multiplier = (
        RISK_LEVEL_MULTIPLIERS[org_profile["internet_exposure"]]
        * RISK_LEVEL_MULTIPLIERS[org_profile["third_party_dependency"]]
    )
    impact_multiplier = (
        RISK_LEVEL_MULTIPLIERS[org_profile["data_sensitivity"]]
        * RISK_LEVEL_MULTIPLIERS[org_profile["regulatory_intensity"]]
    )

    contextualized["frequency"] = scale_range(
        contextualized["frequency"],
        frequency_multiplier,
    )
    contextualized["impact"] = scale_range(
        contextualized["impact"],
        impact_multiplier,
    )

    assumptions = [
        {
            "name": "Internet exposure frequency adjustment",
            "basis": org_profile["internet_exposure"],
            "multiplier": RISK_LEVEL_MULTIPLIERS[org_profile["internet_exposure"]],
            "evidence_type": "estimated",
            "note": "Minimal heuristic; replace with benchmark-backed calibration before production use.",
        },
        {
            "name": "Third-party dependency frequency adjustment",
            "basis": org_profile["third_party_dependency"],
            "multiplier": RISK_LEVEL_MULTIPLIERS[org_profile["third_party_dependency"]],
            "evidence_type": "estimated",
            "note": "Minimal heuristic; replace with benchmark-backed calibration before production use.",
        },
        {
            "name": "Data sensitivity impact adjustment",
            "basis": org_profile["data_sensitivity"],
            "multiplier": RISK_LEVEL_MULTIPLIERS[org_profile["data_sensitivity"]],
            "evidence_type": "estimated",
            "note": "Minimal heuristic; replace with benchmark-backed calibration before production use.",
        },
        {
            "name": "Regulatory intensity impact adjustment",
            "basis": org_profile["regulatory_intensity"],
            "multiplier": RISK_LEVEL_MULTIPLIERS[org_profile["regulatory_intensity"]],
            "evidence_type": "estimated",
            "note": "Minimal heuristic; replace with benchmark-backed calibration before production use.",
        },
    ]

    return contextualized, assumptions


def summarize_provenance(provenance):
    records = provenance["records"]
    confidence = min(records, key=lambda r: CONFIDENCE_ORDER[r["confidence"]])["confidence"]
    evidence_types = sorted({record["evidence_type"] for record in records})

    return {
        "scenario_name": provenance["scenario_name"],
        "summary": provenance.get("summary", ""),
        "record_count": len(records),
        "evidence_types": evidence_types,
        "confidence": confidence,
        "records": records,
    }


def build_report(
    scenario,
    contextualized_scenario,
    org_profile,
    control_profile,
    provenance,
    assumptions,
    baseline_stats,
    controlled_stats,
    delta,
    evidence_match=None,
):
    provenance_summary = summarize_provenance(provenance)
    control_assumptions = [
        {
            "name": "Control profile assumption",
            "basis": "control_profile",
            "evidence_type": "estimated",
            "note": assumption,
        }
        for assumption in control_profile.get("assumptions", [])
    ]

    return {
        "report_type": "contextual_analysis",
        "generated_at": datetime.now().isoformat(),
        "scenario": {
            "metadata": scenario.get("metadata", {}),
            "base_parameters": {
                "frequency": scenario["frequency"],
                "impact": scenario["impact"],
            },
            "contextualized_parameters": {
                "frequency": contextualized_scenario["frequency"],
                "impact": contextualized_scenario["impact"],
            },
        },
        "org_context": org_profile,
        "control_context": control_profile,
        "key_assumptions": assumptions + control_assumptions,
        "source_provenance_summary": provenance_summary,
        "evidence_match": evidence_match,
        "confidence": {
            "overall": provenance_summary["confidence"],
            "note": "Overall confidence is the lowest confidence among supplied provenance records.",
        },
        "baseline_results": baseline_stats,
        "control_adjusted_results": controlled_stats,
        "delta": delta,
    }


def run_contextual_analysis(
    scenario_path,
    org_profile_path,
    control_profile_path,
    provenance_path,
    trials=10000,
    dist_type="pert",
    seed=None,
    threat=None,
    evidence_path=None,
):
    scenario = load_and_validate(scenario_path)
    org_profile = load_org_profile(org_profile_path)
    control_profile = load_control_profile(control_profile_path)
    controls = load_controls(control_profile_path)
    provenance = load_provenance(provenance_path)
    evidence_match = None

    if evidence_path is not None:
        if threat is None:
            raise ValueError("threat is required when evidence_path is provided")
        evidence_records = load_evidence_records(evidence_path)
        evidence_match = summarize_match(match_evidence(evidence_records, org_profile, threat))

    contextualized_scenario, assumptions = contextualize_scenario(scenario, org_profile)
    controlled_scenario = apply_controls(contextualized_scenario, controls)

    baseline_seed = seed
    controlled_seed = seed

    _, baseline_results = run_simulation(
        contextualized_scenario,
        trials=trials,
        dist_type=dist_type,
        rng=None if baseline_seed is None else random.Random(baseline_seed),
    )
    _, controlled_results = run_simulation(
        controlled_scenario,
        trials=trials,
        dist_type=dist_type,
        rng=None if controlled_seed is None else random.Random(controlled_seed),
    )

    baseline_stats = compute_stats(baseline_results)
    controlled_stats = compute_stats(controlled_results)
    delta = compare_runs(baseline_stats, controlled_stats)

    return build_report(
        scenario,
        contextualized_scenario,
        org_profile,
        control_profile,
        provenance,
        assumptions,
        baseline_stats,
        controlled_stats,
        delta,
        evidence_match=evidence_match,
    )


def write_contextual_report(report, output_path=None, output_dir=RESULTS_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"contextual_report_{timestamp}.json"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)

    return output_path
