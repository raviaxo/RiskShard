from collections import Counter
from pathlib import Path

from engine.data_packs import build_data_pack_manifest
from engine.evidence import load_evidence_records
from engine.evidence_packs import build_evidence_pack_registry
from engine.experience import rank_top_risks
from engine.governance import build_data_feed_inventory
from engine.profiles import load_org_profile, load_yaml_file
from engine.risk_modules import load_risk_modules
from engine.scenarios import summarize_scenario_stages


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORG_PROFILE = PROJECT_ROOT / "org_profiles" / "au_finance_midmarket.yaml"


def build_readiness_dashboard(root=PROJECT_ROOT, org_profile_path=DEFAULT_ORG_PROFILE):
    root = Path(root)
    org_profile_path = Path(org_profile_path)
    evidence_records = load_evidence_records(root / "evidence")
    feeds = build_data_feed_inventory(
        registry_path=root / "sources" / "registry.yaml",
        manifest_path=root / "sources" / "manifest.json",
        evidence_path=root / "evidence",
    )
    top_risks = rank_top_risks(
        org_profile_path,
        evidence_path=root / "evidence",
        manifest_path=root / "sources" / "manifest.json",
        threat_library_path=root / "threat_library" / "starter_pack.yaml",
        calibration_dir=root / "calibrations",
    )
    pack = build_data_pack_manifest(root)
    org_profile = load_org_profile(org_profile_path)
    modules = load_risk_modules(root)
    evidence_packs = build_evidence_pack_registry(root)

    dashboard = {
        "org_profile": {
            "path": str(org_profile_path.relative_to(root)),
            "name": org_profile.get("metadata", {}).get("name"),
            "industry": org_profile["industry"],
            "country": org_profile["country"],
            "employees": org_profile["employees"],
            "regulatory_intensity": org_profile["regulatory_intensity"],
        },
        "coverage": coverage_summary(evidence_records),
        "scenarios": {
            "stage_counts": summarize_scenario_stages(root),
        },
        "risk_modules": {
            "module_count": len(modules),
            "status_counts": dict(Counter(module["status"] for module in modules)),
            "threats": sorted({module["threat"] for module in modules}),
        },
        "evidence_packs": {
            "pack_count": evidence_packs["pack_count"],
            "freshness_counts": dict(Counter(
                pack["freshness_status"] for pack in evidence_packs["packs"]
            )),
            "low_confidence_packs": [
                pack["module_id"]
                for pack in evidence_packs["packs"]
                if pack["pack_confidence"] == "low"
            ],
        },
        "top_risks": top_risks,
        "feed_governance": {
            "feed_count": feeds["feed_count"],
            "status_counts": feeds["status_counts"],
            "problem_feeds": [
                feed
                for feed in feeds["feeds"]
                if feed["renewal_status"] != "current"
            ],
        },
        "data_pack": {
            "pack_version": pack["pack_version"],
            "fingerprint": pack["fingerprint"],
            "file_count": pack["file_count"],
        },
        "localization": localization_summary(evidence_records, root),
        "contributor": contributor_summary(root),
        "install_release": install_release_summary(root),
    }
    dashboard["readiness_gate"] = readiness_gate(dashboard)
    dashboard["next_actions"] = next_actions(dashboard)
    return dashboard


def coverage_summary(records):
    threats = Counter()
    countries = Counter()
    industries = Counter()
    evidence_types = Counter(record["evidence_type"] for record in records)

    for record in records:
        applicability = record["applicability"]
        for threat in applicability["threats"]:
            threats[threat] += 1
        for country in applicability["countries"]:
            countries[country] += 1
        for industry in applicability["industries"]:
            industries[industry] += 1

    direct_records = [
        record for record in records
        if record["parameter"] in {
            "frequency.min",
            "frequency.likely",
            "frequency.max",
            "impact.min",
            "impact.likely",
            "impact.max",
        }
    ]

    return {
        "evidence_records": len(records),
        "direct_parameter_records": len(direct_records),
        "source_backed_records": evidence_types["source_backed"],
        "estimated_records": evidence_types["estimated"],
        "synthetic_records": evidence_types["synthetic"],
        "threats": dict(sorted(threats.items())),
        "countries": dict(sorted(countries.items())),
        "industries": dict(sorted(industries.items())),
    }


def localization_summary(records, root):
    currencies = sorted({record.get("currency") for record in records if record.get("currency")})
    countries = sorted({
        country
        for record in records
        for country in record["applicability"]["countries"]
        if country not in {"global"}
    })
    fx_rates = load_yaml_file(root / "calibrations" / "fx_rates.yaml")
    fx_covered_currencies = sorted({
        currency
        for rate in fx_rates.get("rates", [])
        for currency in [rate.get("from"), rate.get("to")]
        if currency
    })
    return {
        "covered_countries": countries,
        "currencies_in_evidence": currencies,
        "fx_covered_currencies": fx_covered_currencies,
        "fx_missing_currencies": sorted(set(currencies) - set(fx_covered_currencies)),
        "fx_rate_count": len(fx_rates.get("rates", [])),
        "needs": [
            "country-specific source trust policy",
            "inflation assumptions",
            "local breach/regulatory regime metadata",
        ],
    }


def contributor_summary(root):
    docs = {
        "contributing": (root / "docs" / "CONTRIBUTING.md").exists(),
        "global_readiness": (root / "docs" / "GLOBAL_READINESS_ROADMAP.md").exists(),
    }
    return {
        "docs": docs,
        "next_needed": [
            "guided source/extraction/evidence/calibration preflight command",
            "example pull request path for a second country or threat pack",
            "pack release checklist",
        ],
    }


def install_release_summary(root):
    pyproject_exists = (root / "pyproject.toml").exists()
    return {
        "pyproject": pyproject_exists,
        "installable_commands": pyproject_exists,
        "next_needed": [] if pyproject_exists else [
            "add pyproject.toml with console scripts",
            "document installed command names",
            "pin data-pack release manifest",
        ],
    }


def readiness_gate(dashboard):
    coverage = dashboard["coverage"]
    problem_feeds = dashboard["feed_governance"]["problem_feeds"]
    runnable = [
        risk for risk in dashboard["top_risks"]
        if risk["status"] in {"calibrated", "calibrated_with_assumptions"}
    ]

    if not runnable:
        return {
            "status": "blocked",
            "summary": "No starter threat has enough direct coverage and calibration profile support.",
        }
    if problem_feeds:
        return {
            "status": "needs_source_review",
            "summary": "A calibrated run is possible, but at least one governed source feed needs review.",
        }
    if coverage["estimated_records"] > coverage["source_backed_records"]:
        return {
            "status": "needs_assumption_review",
            "summary": "A calibrated run is possible, but estimated evidence still outweighs source-backed evidence.",
        }
    return {
        "status": "ready_for_local_calibrated_run",
        "summary": "The local pack is ready for a calibrated run with current governed feeds.",
    }


def next_actions(dashboard, limit=7):
    actions = []
    coverage = dashboard["coverage"]
    problem_feeds = dashboard["feed_governance"]["problem_feeds"]
    localization = dashboard["localization"]
    install = dashboard["install_release"]

    if problem_feeds:
        feed_names = ", ".join(feed["id"] for feed in problem_feeds[:3])
        actions.append({
            "priority": "P0",
            "area": "source governance",
            "title": "Restore governed source feed health",
            "detail": f"Review or refresh {feed_names}. Calibration should keep warning until source status is clean.",
            "command": "python scripts/gather_sources.py",
        })

    for risk in dashboard["top_risks"]:
        if risk["status"] == "calibrated":
            continue
        if risk["assumption_parameters"]:
            title = f"Replace assumptions for {risk['label']}"
            detail = "Add reviewed source-backed frequency and impact evidence before treating this shard as global-ready."
        elif risk["missing_parameters"]:
            title = f"Fill missing direct evidence for {risk['label']}"
            detail = "Cover frequency.min/likely/max and impact.min/likely/max with honest evidence records."
        elif not risk["calibration_profile_exists"]:
            title = f"Add calibration profile for {risk['label']}"
            detail = "Create a small calibration profile that selects the best reviewed evidence for this org context."
        else:
            title = f"Review readiness for {risk['label']}"
            detail = risk["next_steps"][0]
        actions.append({
            "priority": "P1" if risk["direct_coverage"] >= 4 else "P2",
            "area": "risk coverage",
            "title": title,
            "detail": detail,
            "command": f"python scripts/readiness_dashboard.py",
        })

    if coverage["estimated_records"] > coverage["source_backed_records"]:
        actions.append({
            "priority": "P1",
            "area": "evidence quality",
            "title": "Improve the source-backed evidence ratio",
            "detail": (
                f"{coverage['estimated_records']} estimated records vs "
                f"{coverage['source_backed_records']} source-backed records. Keep estimates labeled, but replace the highest-impact ones first."
            ),
            "command": "python scripts/validate_evidence.py",
        })

    if len(localization["covered_countries"]) < 2:
        actions.append({
            "priority": "P2",
            "area": "global localization",
            "title": "Add a second-country evidence pack",
            "detail": "Prove the model can localize beyond AU by adding country-specific sources, currency assumptions, and extraction notes.",
            "command": "python scripts/contributor_preflight.py",
        })

    if localization["fx_missing_currencies"]:
        actions.append({
            "priority": "P2",
            "area": "currency",
            "title": "Map every evidence currency to explicit FX assumptions",
            "detail": (
                "Missing FX coverage for "
                + ", ".join(localization["fx_missing_currencies"])
                + ". Global shards need visible currency conversion assumptions before cross-country comparison."
            ),
            "command": "python scripts/data_governance.py",
        })

    if not install["pyproject"]:
        actions.append({
            "priority": "P2",
            "area": "distribution",
            "title": "Make the CLI installable",
            "detail": "Add package metadata and console entry points so practitioners can run RiskShard outside this checkout.",
            "command": "python -m pip install -e .",
        })

    actions.append({
        "priority": "P3",
        "area": "release discipline",
        "title": "Cut a named data-pack release",
        "detail": "Use the fingerprint as the pin for scenario reviews, demos, and contributor pull requests.",
        "command": "python scripts/data_pack_manifest.py",
    })

    return sorted(actions, key=action_sort_key)[:limit]


def action_sort_key(action):
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return (priority_rank.get(action["priority"], 9), action["area"], action["title"])


def format_readiness_dashboard(dashboard):
    coverage = dashboard["coverage"]
    feeds = dashboard["feed_governance"]
    pack = dashboard["data_pack"]
    install = dashboard["install_release"]
    gate = dashboard["readiness_gate"]
    scenario_counts = dashboard["scenarios"]["stage_counts"]
    module_counts = dashboard["risk_modules"]["status_counts"]
    pack_counts = dashboard["evidence_packs"]["freshness_counts"]
    lines = [
        "Global readiness dashboard",
        f"Org: {dashboard['org_profile']['name']} ({dashboard['org_profile']['country']} / {dashboard['org_profile']['industry']})",
        "",
        f"Gate: {gate['status']} - {gate['summary']}",
        "",
        f"Evidence records: {coverage['evidence_records']} total; {coverage['source_backed_records']} source-backed; {coverage['estimated_records']} estimated",
        f"Threat coverage: {', '.join(sorted(coverage['threats']))}",
        f"Countries: {', '.join(dashboard['localization']['covered_countries']) or 'none'}",
        "",
        f"Feeds: {feeds['feed_count']} ({format_counts(feeds['status_counts'])})",
        f"Scenarios: {format_counts(scenario_counts)}",
        f"Risk modules: {dashboard['risk_modules']['module_count']} ({format_counts(module_counts)})",
        f"Evidence packs: {dashboard['evidence_packs']['pack_count']} ({format_counts(pack_counts)})",
        f"Data pack: {pack['pack_version']} {pack['fingerprint'][:12]} files={pack['file_count']}",
        f"Installable package: {install['pyproject']}",
        "",
        "Top risk readiness",
    ]
    for risk in dashboard["top_risks"]:
        lines.append(
            f"- {risk['label']}: {risk['status']} "
            f"direct={risk['direct_coverage']}/{risk['direct_total']} "
            f"assumptions={risk['assumption_parameters']}"
        )
    lines.extend(["", "Next actions"])
    for action in dashboard["next_actions"]:
        lines.append(f"- {action['priority']} {action['title']} ({action['area']})")
    return "\n".join(lines) + "\n"


def format_next_actions(dashboard):
    gate = dashboard["readiness_gate"]
    lines = [
        "Next best actions",
        f"Gate: {gate['status']}",
        gate["summary"],
        "",
    ]
    for action in dashboard["next_actions"]:
        lines.extend([
            f"- {action['priority']} {action['title']}",
            f"  area: {action['area']}",
            f"  why: {action['detail']}",
            f"  command: {action['command']}",
        ])
    return "\n".join(lines) + "\n"


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
