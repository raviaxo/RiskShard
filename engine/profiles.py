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


def load_org_profile(path, schema_path=ORG_PROFILE_SCHEMA_PATH):
    profile = load_yaml_file(path)
    validate(instance=profile, schema=load_json_schema(schema_path))
    return profile


def load_provenance(path, schema_path=PROVENANCE_SCHEMA_PATH):
    provenance = load_yaml_file(path)
    validate(instance=provenance, schema=load_json_schema(schema_path))
    return provenance
