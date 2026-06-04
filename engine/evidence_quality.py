import json
from pathlib import Path

from engine.evidence import load_evidence_records


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "sources" / "manifest.json"


def load_source_manifest(path=DEFAULT_MANIFEST_PATH):
    with open(path, "r") as f:
        manifest = json.load(f)
    return {source["id"]: source for source in manifest["sources"]}


def validate_evidence_quality(evidence_path, manifest_path=DEFAULT_MANIFEST_PATH):
    records = load_evidence_records(evidence_path)
    manifest_by_id = load_source_manifest(manifest_path)
    issues = []

    for record in records:
        issues.extend(validate_record_quality(record, manifest_by_id))

    return issues


def validate_record_quality(record, manifest_by_id):
    issues = []
    record_id = record["id"]

    if record["unit"] == "currency" and not record.get("currency"):
        issues.append(issue("error", "currency_missing", record_id, "Currency evidence must include currency."))

    if record["evidence_type"] != "source_backed":
        return issues

    source_id = record.get("source_id")
    if not source_id:
        issues.append(issue("error", "source_id_missing", record_id, "Source-backed evidence must include source_id."))
        return issues

    source_ids = record.get("source_ids") or [source_id]
    if source_id not in source_ids:
        issues.append(
            issue(
                "error",
                "primary_source_id_missing_from_source_ids",
                record_id,
                "source_ids must include the primary source_id.",
            )
        )

    for related_source_id in source_ids:
        if related_source_id not in manifest_by_id:
            issues.append(
                issue(
                    "error",
                    "source_id_unknown",
                    record_id,
                    f"Unknown source_id: {related_source_id}",
                )
            )

    source = manifest_by_id.get(source_id)
    if source is None:
        issues.append(issue("error", "source_id_unknown", record_id, f"Unknown source_id: {source_id}"))
        return issues

    if not record.get("citation_detail"):
        issues.append(issue("error", "citation_detail_missing", record_id, "Source-backed evidence must include citation_detail."))

    if record.get("publication_date") != source.get("publication_date"):
        issues.append(
            issue(
                "error",
                "publication_date_mismatch",
                record_id,
                f"Evidence publication_date {record.get('publication_date')} does not match manifest {source.get('publication_date')}.",
            )
        )

    source_urls = {source.get("url"), source.get("final_url")}
    if record.get("source_url_or_citation") not in source_urls:
        issues.append(
            issue(
                "error",
                "source_url_mismatch",
                record_id,
                "Evidence source_url_or_citation must match the manifest URL or final URL.",
            )
        )

    if source.get("status") != "fetched":
        issues.append(
            issue(
                "warning",
                "source_not_fetched",
                record_id,
                f"Manifest source {source_id} was not fetched in the latest gather run.",
            )
        )
        if "latest source gather did not retrieve" not in record.get("limitations", ""):
            issues.append(
                issue(
                    "error",
                    "source_not_fetched_not_disclosed",
                    record_id,
                    "Evidence must disclose when the latest source gather did not retrieve the raw artifact.",
                )
            )

    return issues


def issue(severity, code, record_id, message):
    return {
        "severity": severity,
        "code": code,
        "record_id": record_id,
        "message": message,
    }


def has_errors(issues):
    return any(item["severity"] == "error" for item in issues)
