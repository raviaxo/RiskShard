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

    issues.extend(validate_artifact_verification(record, source))

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


def validate_artifact_verification(record, source):
    """ADR-0026 — a re-read is declared on the record and pinned to the bytes read.

    The two fields travel together or not at all. Their absence means nobody has
    checked this record against the publisher's file, which is not the same as
    the record being clean, so absence is never reported here.

    A hash that no longer matches the manifest is a **warning**, deliberately.
    It is the design working: the publisher reissued the file, so our reading is
    a reading of a document that is no longer the stored one and the record drops
    back to unverified. That is something to look at again, not something wrong.
    Malformed input is an error, because that is a typo rather than a finding.
    """
    issues = []
    record_id = record["id"]
    verified_at = record.get("artifact_verified_at")
    verified_sha = record.get("artifact_verified_sha256")

    if not verified_at and not verified_sha:
        return issues

    if bool(verified_at) != bool(verified_sha):
        issues.append(
            issue(
                "error",
                "artifact_verification_incomplete",
                record_id,
                "artifact_verified_at and artifact_verified_sha256 must be given together: "
                "a date without a hash cannot expire, and a hash without a date cannot be audited.",
            )
        )
        return issues

    if not _looks_like_a_date(verified_at):
        issues.append(
            issue(
                "error",
                "artifact_verified_at_malformed",
                record_id,
                f"artifact_verified_at must be YYYY-MM-DD, got {verified_at!r}.",
            )
        )

    if not _looks_like_a_sha256(verified_sha):
        issues.append(
            issue(
                "error",
                "artifact_verified_sha256_malformed",
                record_id,
                "artifact_verified_sha256 must be 64 lowercase hex characters.",
            )
        )
        return issues

    stored = (source.get("sha256") or "").lower()
    if not stored:
        issues.append(
            issue(
                "warning",
                "artifact_verification_unpinnable",
                record_id,
                "The manifest holds no sha256 for this source, so the recorded verification "
                "cannot expire when the publisher reissues the file.",
            )
        )
    elif stored != verified_sha:
        issues.append(
            issue(
                "warning",
                "artifact_verification_stale",
                record_id,
                f"Verified on {verified_at} against a file whose hash is no longer the stored one. "
                "The publisher has reissued it; the record needs re-reading.",
            )
        )

    return issues


def _looks_like_a_date(value):
    import datetime

    try:
        datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _looks_like_a_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value
    )


def issue(severity, code, record_id, message):
    return {
        "severity": severity,
        "code": code,
        "record_id": record_id,
        "message": message,
    }


def has_errors(issues):
    return any(item["severity"] == "error" for item in issues)
