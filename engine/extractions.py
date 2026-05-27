import json
from pathlib import Path

from jsonschema import validate

from engine.evidence import load_evidence_records
from engine.evidence_quality import load_source_manifest
from engine.profiles import load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTION_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "extraction_schema.json"
EXTRACTIONS_DIR = PROJECT_ROOT / "extractions"


def load_schema(path=EXTRACTION_SCHEMA_PATH):
    with open(path, "r") as f:
        return json.load(f)


def extraction_files(path):
    path = Path(path)
    if path.is_dir():
        return sorted(path.rglob("*.yaml"))
    return [path]


def load_extractions(path=EXTRACTIONS_DIR, schema_path=EXTRACTION_SCHEMA_PATH):
    schema = load_schema(schema_path)
    records = []

    for extraction_path in extraction_files(path):
        data = load_yaml_file(extraction_path)
        validate(instance=data, schema=schema)
        for record in data["extractions"]:
            record = dict(record)
            record["_source_file"] = str(extraction_path)
            records.append(record)

    return records


def validate_extractions(extractions_path, evidence_path, manifest_path):
    extractions = load_extractions(extractions_path)
    evidence_ids = {record["id"] for record in load_evidence_records(evidence_path)}
    manifest_by_id = load_source_manifest(manifest_path)
    issues = []

    for extraction in extractions:
        source = manifest_by_id.get(extraction["source_id"])
        if source is None:
            issues.append(extraction_issue("error", "source_id_unknown", extraction["id"], "Unknown source_id."))
        elif extraction["publication_date"] != source["publication_date"]:
            issues.append(
                extraction_issue(
                    "error",
                    "publication_date_mismatch",
                    extraction["id"],
                    "Extraction publication_date must match the source manifest.",
                )
            )
        elif source["status"] != "fetched":
            issues.append(
                extraction_issue(
                    "warning",
                    "source_not_fetched",
                    extraction["id"],
                    "Extraction references a source that was not fetched in the latest manifest.",
                )
            )
            if "did not retrieve" not in extraction.get("limitations", "").lower():
                issues.append(
                    extraction_issue(
                        "error",
                        "source_not_fetched_not_disclosed",
                        extraction["id"],
                        "Extraction must disclose when the latest gather did not retrieve the raw artifact.",
                    )
                )

        for evidence_id in extraction["evidence_record_ids"]:
            if evidence_id not in evidence_ids:
                issues.append(
                    extraction_issue(
                        "error",
                        "evidence_record_missing",
                        extraction["id"],
                        f"Extraction references missing evidence record: {evidence_id}",
                    )
                )

    return issues


def extraction_issue(severity, code, extraction_id, message):
    return {
        "severity": severity,
        "code": code,
        "extraction_id": extraction_id,
        "message": message,
    }
