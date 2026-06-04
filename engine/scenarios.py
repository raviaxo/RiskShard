from pathlib import Path

import yaml
from jsonschema import validate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "shard_schema.json"

SCENARIO_STAGE_LABELS = {
    "governed_starter": "governed starter",
    "demo_fixture": "demo fixture",
}


def scenario_paths(root=PROJECT_ROOT):
    return sorted((Path(root) / "scenarios").glob("*.yaml"))


def scenario_stage(config):
    return config.get("metadata", {}).get("scenario_stage", "demo_fixture")


def scenario_stage_label(config):
    return SCENARIO_STAGE_LABELS.get(scenario_stage(config), scenario_stage(config))


def load_scenario_summaries(root=PROJECT_ROOT):
    rows = []
    schema = load_schema(Path(root) / "schemas" / "shard_schema.json")
    for path in scenario_paths(root):
        config = load_scenario(path, schema)
        rows.append({
            "id": path.stem,
            "name": config["metadata"]["name"],
            "path": path,
            "stage": scenario_stage(config),
            "stage_label": scenario_stage_label(config),
            "benchmark_status": config.get("metadata", {}).get("benchmark_status", "unspecified"),
        })
    return rows


def load_schema(path=SCHEMA_PATH):
    with open(path, "r") as f:
        import json

        return json.load(f)


def load_scenario(path, schema=None):
    schema = schema or load_schema()
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    validate(instance=config, schema=schema)
    return config


def summarize_scenario_stages(root=PROJECT_ROOT):
    counts = {}
    for row in load_scenario_summaries(root):
        counts[row["stage"]] = counts.get(row["stage"], 0) + 1
    return counts
