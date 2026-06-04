from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from engine.evidence import load_evidence_records
from engine.evidence_quality import load_source_manifest
from engine.profiles import load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "sources" / "registry.yaml"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "sources" / "manifest.json"
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "evidence"

DEFAULT_REVIEW_INTERVAL_DAYS = {
    "breach_report": 365,
    "cyber_loss_research": 365,
    "government_report": 365,
    "industry_survey": 365,
    "law_enforcement_report": 365,
    "official_statistical_data": 365,
    "ransomware_research": 365,
    "regulator_report": 180,
    "regulator_standard": 365,
    "scam_report": 365,
}

DEFAULT_TRUST_TIER = {
    "breach_report": "medium",
    "cyber_loss_research": "medium",
    "government_report": "high",
    "industry_survey": "medium",
    "law_enforcement_report": "high",
    "official_statistical_data": "high",
    "ransomware_research": "medium",
    "regulator_report": "high",
    "regulator_standard": "high",
    "scam_report": "high",
}

CONFIDENCE_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}
EVIDENCE_TYPE_ORDER = {"synthetic": 0, "estimated": 1, "source_backed": 2}


def build_data_feed_inventory(
    *,
    registry_path=DEFAULT_REGISTRY_PATH,
    manifest_path=DEFAULT_MANIFEST_PATH,
    evidence_path=DEFAULT_EVIDENCE_DIR,
    today=None,
):
    today = today or date.today()
    registry = load_yaml_file(registry_path)
    manifest_by_id = load_source_manifest(manifest_path)
    evidence_by_source = group_source_backed_evidence(load_evidence_records(evidence_path))
    feeds = []

    for source in registry["sources"]:
        source_id = source["id"]
        manifest = manifest_by_id.get(source_id, {})
        evidence_records = evidence_by_source.get(source_id, [])
        interval_days = source.get(
            "refresh_interval_days",
            DEFAULT_REVIEW_INTERVAL_DAYS.get(source["source_type"], 365),
        )
        gathered_at = manifest.get("gathered_at")
        renewal_due = renewal_due_date(gathered_at, interval_days)
        status = governance_status(manifest, renewal_due, today)
        confidence = summarize_evidence_confidence(evidence_records)
        evidence_types = Counter(record["evidence_type"] for record in evidence_records)

        feeds.append({
            "id": source_id,
            "title": source["title"],
            "publisher": source["publisher"],
            "source_type": source["source_type"],
            "trust_tier": source.get(
                "trust_tier",
                DEFAULT_TRUST_TIER.get(source["source_type"], "medium"),
            ),
            "source_status": manifest.get("status", "not_gathered"),
            "publication_date": source["publication_date"],
            "source_gathered_at": gathered_at,
            "riskshard_evidence_ingested_at": latest_date(
                record.get("extraction_date") for record in evidence_records
            ),
            "renewal_due": renewal_due.isoformat() if renewal_due else None,
            "renewal_status": status,
            "refresh_interval_days": interval_days,
            "evidence_record_count": len(evidence_records),
            "evidence_confidence": confidence,
            "evidence_type_counts": dict(sorted(evidence_types.items())),
            "raw_path": manifest.get("raw_path"),
            "sha256": manifest.get("sha256"),
            "final_url": manifest.get("final_url"),
            "error": manifest.get("error"),
        })

    feeds.sort(key=feed_sort_key)
    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "feed_count": len(feeds),
        "status_counts": dict(Counter(feed["renewal_status"] for feed in feeds)),
        "feeds": feeds,
    }


def group_source_backed_evidence(records):
    grouped = {}
    for record in records:
        source_ids = record.get("source_ids") or [record.get("source_id")]
        for source_id in {source_id for source_id in source_ids if source_id}:
            grouped.setdefault(source_id, []).append(record)
    return grouped


def renewal_due_date(gathered_at, interval_days):
    gathered_date = parse_date(gathered_at)
    if gathered_date is None:
        return None
    return gathered_date + timedelta(days=interval_days)


def governance_status(manifest, renewal_due, today):
    if not manifest:
        return "not_gathered"
    if manifest.get("status") != "fetched":
        return "gather_error"
    if renewal_due is None:
        return "unknown"
    if renewal_due < today:
        return "overdue"
    if renewal_due <= today + timedelta(days=30):
        return "renew_soon"
    return "current"


def summarize_evidence_confidence(records):
    if not records:
        return "none"
    return max((record["confidence"] for record in records), key=lambda value: CONFIDENCE_ORDER[value])


def latest_date(values):
    parsed = [parse_date(value) for value in values if value]
    parsed = [value for value in parsed if value is not None]
    if not parsed:
        return None
    return max(parsed).isoformat()


def parse_date(value):
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()


def feed_sort_key(feed):
    status_rank = {
        "gather_error": 0,
        "not_gathered": 1,
        "overdue": 2,
        "renew_soon": 3,
        "unknown": 4,
        "current": 5,
    }
    return (status_rank.get(feed["renewal_status"], 9), feed["id"])


def format_data_feed_inventory(inventory):
    lines = [
        "Data feed governance",
        f"Feeds: {inventory['feed_count']}",
        "Statuses: " + format_counts(inventory["status_counts"]),
        "",
    ]
    for feed in inventory["feeds"]:
        lines.extend(format_feed_summary(feed))
    return "\n".join(lines).rstrip() + "\n"


def format_feed_summary(feed):
    evidence_counts = format_counts(feed["evidence_type_counts"]) or "none"
    return [
        f"- {feed['id']}: {feed['renewal_status']}",
        f"  source: {feed['publisher']} / {feed['source_type']} / trust={feed['trust_tier']}",
        f"  published: {feed['publication_date']}; source_gathered: {feed['source_gathered_at'] or 'never'}; renewal_due: {feed['renewal_due'] or 'n/a'}",
        f"  evidence_ingested: {feed['riskshard_evidence_ingested_at'] or 'none'}; evidence_confidence: {feed['evidence_confidence']}; records: {feed['evidence_record_count']} ({evidence_counts})",
    ]


def format_feed_detail(feed):
    lines = format_feed_summary(feed)
    lines.extend([
        f"  raw_path: {feed['raw_path'] or 'none'}",
        f"  sha256: {feed['sha256'] or 'none'}",
        f"  final_url: {feed['final_url'] or 'none'}",
    ])
    if feed.get("error"):
        lines.append(f"  error: {feed['error']}")
    return "\n".join(lines) + "\n"


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
