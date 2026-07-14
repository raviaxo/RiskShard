import re
from pathlib import Path

from engine.profiles import load_yaml_file
from engine.project_paths import find_project_root


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_DIR = PROJECT_ROOT / "taxonomies"


def normalize_key(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def load_taxonomy(name, taxonomy_dir=None):
    taxonomy_dir = Path(taxonomy_dir) if taxonomy_dir is not None else find_project_root() / "taxonomies"
    path = taxonomy_dir / f"{name}.yaml"
    data = load_yaml_file(path)
    return data["items"]


def load_taxonomies(taxonomy_dir=None):
    return {
        "industries": load_taxonomy("industries", taxonomy_dir),
        "countries": load_taxonomy("countries", taxonomy_dir),
        "company_sizes": load_taxonomy("company_sizes", taxonomy_dir),
        "threats": load_taxonomy("threats", taxonomy_dir),
    }


def canonicalize(value, items):
    target = normalize_key(value)

    for item in items:
        candidates = [item["id"], item["label"]] + item.get("aliases", [])
        if target in {normalize_key(candidate) for candidate in candidates}:
            return item["id"]

    raise ValueError(f"Unknown taxonomy value: {value}")


def company_size_for_employees(employees, size_items):
    for item in size_items:
        if item["id"] == "all":
            continue

        minimum = item.get("employee_min", 1)
        maximum = item.get("employee_max")
        if employees >= minimum and (maximum is None or employees <= maximum):
            return item["id"]

    raise ValueError(f"No company size band matches employees={employees}")


def normalize_context(org_profile, threat, taxonomies=None):
    taxonomies = taxonomies or load_taxonomies()

    return {
        "industry": canonicalize(org_profile["industry"], taxonomies["industries"]),
        "country": canonicalize(org_profile["country"], taxonomies["countries"]),
        "company_size": company_size_for_employees(
            org_profile["employees"],
            taxonomies["company_sizes"],
        ),
        "threat": canonicalize(threat, taxonomies["threats"]),
    }
