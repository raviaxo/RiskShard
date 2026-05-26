import json
from pathlib import Path

from jsonschema import validate

from engine.profiles import load_yaml_file
from engine.taxonomy import normalize_context


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "evidence_record_schema.json"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

CONFIDENCE_SCORE = {"low": 1, "medium": 2, "high": 3}
EVIDENCE_TYPE_SCORE = {"synthetic": 0, "estimated": 1, "source_backed": 2}


def load_schema(schema_path=EVIDENCE_SCHEMA_PATH):
    with open(schema_path, "r") as f:
        return json.load(f)


def evidence_files(path):
    path = Path(path)
    if path.is_dir():
        return sorted(path.rglob("*.yaml"))
    return [path]


def load_evidence_records(path=EVIDENCE_DIR, schema_path=EVIDENCE_SCHEMA_PATH):
    schema = load_schema(schema_path)
    records = []

    for evidence_path in evidence_files(path):
        data = load_yaml_file(evidence_path)
        validate(instance=data, schema=schema)
        for record in data["records"]:
            record = dict(record)
            record["_source_file"] = str(evidence_path)
            records.append(record)

    return records


def match_dimension(values, target, wildcard):
    if target in values:
        return "exact", 3
    if wildcard in values:
        return "fallback", 1
    return "miss", 0


def score_record(record, context):
    applicability = record["applicability"]
    dimensions = {
        "industry": match_dimension(applicability["industries"], context["industry"], "all"),
        "country": match_dimension(applicability["countries"], context["country"], "global"),
        "company_size": match_dimension(
            applicability["company_size_bands"],
            context["company_size"],
            "all",
        ),
        "threat": match_dimension(applicability["threats"], context["threat"], "all"),
    }

    if any(status == "miss" for status, _ in dimensions.values()):
        return None

    applicability_score = sum(score for _, score in dimensions.values())
    evidence_score = EVIDENCE_TYPE_SCORE[record["evidence_type"]]
    confidence_score = CONFIDENCE_SCORE[record["confidence"]]

    return {
        "score": applicability_score + evidence_score + confidence_score,
        "applicability": {
            name: {"match": status, "score": score}
            for name, (status, score) in dimensions.items()
        },
        "evidence_score": evidence_score,
        "confidence_score": confidence_score,
    }


def match_evidence(records, org_profile, threat, parameters=None):
    context = normalize_context(org_profile, threat)
    parameters = set(parameters or [])
    matches = []

    for record in records:
        if parameters and record["parameter"] not in parameters:
            continue

        score = score_record(record, context)
        if score is None:
            continue

        matches.append({
            "record": record,
            "score": score["score"],
            "applicability": score["applicability"],
            "confidence_score": score["confidence_score"],
            "evidence_score": score["evidence_score"],
        })

    matches.sort(key=lambda item: item["score"], reverse=True)

    best_by_parameter = {}
    for match in matches:
        parameter = match["record"]["parameter"]
        if parameter not in best_by_parameter:
            best_by_parameter[parameter] = match

    return {
        "target_context": context,
        "match_count": len(matches),
        "matches": matches,
        "best_by_parameter": best_by_parameter,
    }


def summarize_match(match_result):
    return {
        "target_context": match_result["target_context"],
        "match_count": match_result["match_count"],
        "best_by_parameter": {
            parameter: {
                "id": match["record"]["id"],
                "title": match["record"]["title"],
                "source_id": match["record"].get("source_id"),
                "source_name": match["record"]["source_name"],
                "value": match["record"]["value"],
                "unit": match["record"]["unit"],
                "currency": match["record"].get("currency"),
                "citation_detail": match["record"].get("citation_detail"),
                "confidence": match["record"]["confidence"],
                "evidence_type": match["record"]["evidence_type"],
                "score": match["score"],
                "applicability": match["applicability"],
                "limitations": match["record"]["limitations"],
            }
            for parameter, match in match_result["best_by_parameter"].items()
        },
    }
