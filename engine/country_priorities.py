from collections import Counter
from pathlib import Path

from engine.profiles import load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRIORITY_PATH = PROJECT_ROOT / "taxonomies" / "country_priorities.yaml"


def load_country_priorities(path=DEFAULT_PRIORITY_PATH):
    data = load_yaml_file(path)
    items = sorted(data["items"], key=lambda item: item["rank"])
    return {
        "method": data["method"],
        "items": items,
        "tier_counts": dict(Counter(item["tier"] for item in items)),
        "status_counts": dict(Counter(item["status"] for item in items)),
    }


def top_country_priorities(limit=25, path=DEFAULT_PRIORITY_PATH):
    priorities = load_country_priorities(path)
    return {
        **priorities,
        "items": priorities["items"][:limit],
    }


def find_country_priority(country_id, path=DEFAULT_PRIORITY_PATH):
    country_id = country_id.strip().upper()
    for item in load_country_priorities(path)["items"]:
        if item["country_id"] == country_id or item["label"].upper() == country_id:
            return item
    return None


def format_country_priorities(priorities):
    method = priorities["method"]
    lines = [
        "Country expansion priorities",
        f"Method: {method['version']} ({method['updated']})",
        "Basis: " + ", ".join(method["basis"]),
        "Tiers: " + format_counts(priorities["tier_counts"]),
        "Statuses: " + format_counts(priorities["status_counts"]),
        "",
        "Rank  Country  Tier              Status         Recommended first module",
        "----  -------  ----              ------         ------------------------",
    ]
    for item in priorities["items"]:
        lines.append(
            f"{item['rank']:>4}  {item['country_id']:<7}  {item['tier']:<16} "
            f"{item['status']:<14} {item['recommended_first_module']}"
        )
    return "\n".join(lines) + "\n"


def format_country_priority_detail(item):
    lines = [
        f"Country priority: {item['country_id']} - {item['label']}",
        f"Rank      : {item['rank']}",
        f"Region    : {item['region']}",
        f"Tier      : {item['tier']}",
        f"Status    : {item['status']}",
        f"First mod : {item['recommended_first_module']}",
        f"Why       : {item['why']}",
        f"Contribute: {item['collaboration_prompt']}",
    ]
    if item.get("coverage_summary"):
        lines.append(f"Coverage  : {item['coverage_summary']}")
    if item.get("next_contribution"):
        lines.append(f"Next gap  : {item['next_contribution']}")
    lines.append("")
    return "\n".join(lines)


def format_counts(counts):
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
