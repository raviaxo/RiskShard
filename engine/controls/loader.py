import json
from pathlib import Path
from typing import List

import yaml
from jsonschema import validate

from engine.controls.base import Control
from engine.controls.library import FrequencyReduction, ImpactReduction


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTROL_PROFILE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "control_profile_schema.json"

CONTROL_MAP = {
    "frequency_reduction": FrequencyReduction,
    "impact_reduction": ImpactReduction,
}


def load_control_profile(path: str, schema_path=CONTROL_PROFILE_SCHEMA_PATH) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Empty or invalid YAML file: {path}")

    with open(schema_path, "r") as f:
        schema = json.load(f)

    validate(instance=data, schema=schema)
    return data


def load_controls(path: str) -> List[Control]:
    data = load_control_profile(path)

    controls = []

    for c in data.get("controls", []):
        control_type = c.get("type")

        if control_type not in CONTROL_MAP:
            raise ValueError(f"Unknown control type: {control_type}")

        cls = CONTROL_MAP[control_type]
        params = {"reduction_pct": c["reduction_pct"]}
        controls.append(cls(**params))

    return controls
