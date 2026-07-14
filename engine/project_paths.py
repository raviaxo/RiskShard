import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV_VAR = "RISKSHARD_ROOT"
ROOT_MARKERS = (
    "pyproject.toml",
    "schemas/shard_schema.json",
    "sources/manifest.json",
    "risk_modules",
)


def find_project_root(start=None, *, fallback=PROJECT_ROOT, env_var=ROOT_ENV_VAR):
    """Find the RiskShard checkout that owns scenarios, evidence, and docs."""
    env_root = os.environ.get(env_var)
    if env_root:
        env_path = Path(env_root).expanduser().resolve()
        if looks_like_project_root(env_path):
            return env_path

    for candidate in candidate_roots(start):
        if looks_like_project_root(candidate):
            return candidate

    fallback = Path(fallback).expanduser().resolve()
    if looks_like_project_root(fallback):
        return fallback
    return fallback


def candidate_roots(start=None):
    start_path = Path(start or Path.cwd()).expanduser().resolve()
    candidates = [start_path, *start_path.parents]
    cwd = Path.cwd().expanduser().resolve()
    if cwd not in candidates:
        candidates.extend([cwd, *cwd.parents])
    return candidates


def looks_like_project_root(path):
    path = Path(path)
    return all((path / marker).exists() for marker in ROOT_MARKERS)
