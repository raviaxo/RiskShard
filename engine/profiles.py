import json
from pathlib import Path

import yaml
from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORG_PROFILE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "org_profile_schema.json"
PROVENANCE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "provenance_schema.json"


def load_json_schema(path):
    with open(path, "r") as f:
        return json.load(f)


def load_yaml_file(path):
    path = Path(path)
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Empty or invalid YAML file: {path}")

    return data


def inferred_schema_path(data_path, schema_name):
    data_path = Path(data_path)
    repo_data_dirs = {"control_profiles", "org_profiles", "provenance"}
    root = data_path.parent.parent if data_path.parent.name in repo_data_dirs else PROJECT_ROOT
    candidate = root / "schemas" / schema_name
    return candidate if candidate.exists() else PROJECT_ROOT / "schemas" / schema_name


def load_org_profile(path, schema_path=None):
    schema_path = schema_path or inferred_schema_path(path, "org_profile_schema.json")
    profile = load_yaml_file(path)
    validate(instance=profile, schema=load_json_schema(schema_path))
    return profile


def load_provenance(path, schema_path=None):
    schema_path = schema_path or inferred_schema_path(path, "provenance_schema.json")
    provenance = load_yaml_file(path)
    validate(instance=provenance, schema=load_json_schema(schema_path))
    return provenance
