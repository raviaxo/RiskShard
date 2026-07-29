import hashlib
import json
import random
import statistics
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import validate

from engine.scenarios import scenario_stage, scenario_stage_label


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "shard_schema.json"
RESULTS_DIR = PROJECT_ROOT / "results"
VALID_DISTRIBUTIONS = {"pert", "triangular"}

# Structural methodology caveat, applies to every shard regardless of data.
# Severity is far less predictable from a shard's cell than frequency is; the
# product must not imply the impact tail is as trustworthy as the frequency band.
# See docs/METHODOLOGY.md (frequency/severity asymmetry). Reused across the
# console, executive report, and JSON export so the message stays identical.
IMPACT_UNCERTAINTY_NOTE = (
    "Impact is only weakly predictable from a shard's cell (country, industry, "
    "size, threat); read the P95/P99 loss tail as directional, not precise. "
    "See docs/METHODOLOGY.md."
)

# ADR-0001: shown whenever a scenario carries loss_stages, so a reader knows the
# loss number composes conditional downstream stages (e.g. a regulatory penalty),
# each rare and tail-driving, and can check each stage's provenance.
LOSS_CHAIN_NOTE = (
    "This scenario composes one or more conditional downstream loss stages "
    "(ADR-0001); each stage is gated by its own conditional probability "
    "(source-backed, or an explicitly labeled estimate) and adds to the tail "
    "more than the mean. Read each stage's evidence and confidence separately."
)


def load_schema(schema_path=SCHEMA_PATH):
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found at {schema_path}")

    with open(schema_path, "r") as f:
        return json.load(f)


def load_and_validate(path, schema=None):
    path = Path(path)
    schema = schema or load_schema()

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError(f"Empty or invalid YAML file: {path}")

    validate(instance=config, schema=schema)
    return config


def scenario_files(input_path):
    input_path = Path(input_path)
    if input_path.is_dir():
        return sorted(input_path.glob("*.yaml"))
    return [input_path]


def scenario_fingerprint(config):
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def portable_scenario_key(scenario_path, root=PROJECT_ROOT):
    """Machine-independent identity for a scenario file (ADR-0002).

    Seeds must not depend on where the repository sits on disk, or the same shard
    yields different numbers on different machines and a published figure cannot be
    reproduced by a third party. A scenario stored outside the project root falls
    back to its filename: its directory is user-specific by definition.
    """
    candidate = Path(scenario_path)
    try:
        return candidate.resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return candidate.name


def derive_scenario_seed(base_seed, scenario_path, config, root=PROJECT_ROOT):
    fingerprint = scenario_fingerprint(config)
    payload = f"{base_seed}:{portable_scenario_key(scenario_path, root)}:{fingerprint}"
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8], 16)


def percentile(data, p):
    if not data:
        return 0

    k = int(len(data) * p)
    return data[min(k, len(data) - 1)]


def beta_pert(low, likely, high, confidence=4, rng=None):
    if low >= high:
        return low

    rng = rng or random
    alpha = 1 + confidence * (likely - low) / (high - low)
    beta = 1 + confidence * (high - likely) / (high - low)
    return low + rng.betavariate(alpha, beta) * (high - low)


def sample_range(values, dist_type, rng):
    if dist_type == "pert":
        return beta_pert(values["min"], values["likely"], values["max"], rng=rng)
    if dist_type == "triangular":
        return rng.triangular(values["min"], values["max"], values["likely"])
    raise ValueError(f"Unsupported distribution: {dist_type}")


def run_simulation(config, trials, dist_type="pert", rng=None):
    if trials <= 0:
        raise ValueError("trials must be greater than zero")
    if dist_type not in VALID_DISTRIBUTIONS:
        raise ValueError(f"Unsupported distribution: {dist_type}")

    rng = rng or random.Random()
    impact = config["impact"]
    frequency = config["frequency"]
    # ADR-0001: optional conditional loss stages composed onto the initiating
    # event's impact per trial. Absent loss_stages, behaviour and RNG draws are
    # identical to the single-event model (no extra draws are consumed).
    loss_stages = config.get("loss_stages") or []
    name = config["metadata"]["name"]

    results = []
    for _ in range(trials):
        sampled_frequency = sample_range(frequency, dist_type, rng)
        sampled_impact = sample_range(impact, dist_type, rng)
        for stage in loss_stages:
            stage_probability = sample_range(stage["conditional_probability"], dist_type, rng)
            if rng.random() < stage_probability:
                sampled_impact += sample_range(stage["impact"], dist_type, rng)
        results.append(sampled_frequency * sampled_impact)

    return name, results


def aggregate_portfolio(portfolio_results):
    lengths = {len(v) for v in portfolio_results.values()}
    if len(lengths) != 1:
        raise ValueError("Inconsistent simulation lengths across shards")

    return [sum(x) for x in zip(*portfolio_results.values())]


def compute_stats(results):
    results_sorted = sorted(results)

    return {
        "mean": statistics.mean(results_sorted),
        "p50": statistics.median(results_sorted),
        "p95": percentile(results_sorted, 0.95),
        "p99": percentile(results_sorted, 0.99),
    }


def compute_all_stats(portfolio):
    shard_stats = {}

    for name, results in portfolio.items():
        shard_stats[name] = compute_stats(results)

    aggregate = aggregate_portfolio(portfolio)
    portfolio_stats = compute_stats(aggregate)

    return shard_stats, portfolio_stats, aggregate


def run_portfolio(path, trials=10000, dist_type="pert", seed=None, schema_path=SCHEMA_PATH):
    schema = load_schema(schema_path)
    portfolio = {}
    failures = []
    metadata = {
        "input_path": str(path),
        "trials": trials,
        "distribution": dist_type,
        "reproducibility": {
            "deterministic": seed is not None,
            "base_seed": seed,
            "seed_source": "cli" if seed is not None else None,
            "rng_isolation": "per_scenario" if seed is not None else "per_scenario_nondeterministic",
            "reproduction_command": reproduction_command(path, trials, dist_type, seed),
            "scenarios": [],
        },
    }

    for scenario_path in scenario_files(path):
        try:
            config = load_and_validate(scenario_path, schema)
            scenario_metadata = config.get("metadata", {})
            currency = scenario_metadata.get("currency", "unspecified")
            scenario_seed = None
            if seed is not None:
                scenario_seed = derive_scenario_seed(seed, scenario_path, config)
                rng = random.Random(scenario_seed)
            else:
                rng = random.Random()

            name, results = run_simulation(config, trials, dist_type, rng)
            portfolio[name] = results
            metadata["reproducibility"]["scenarios"].append({
                "name": name,
                "path": str(scenario_path),
                "stage": scenario_stage(config),
                "stage_label": scenario_stage_label(config),
                "benchmark_status": scenario_metadata.get("benchmark_status", "unspecified"),
                "currency": currency,
                "seed": scenario_seed,
                "fingerprint": scenario_fingerprint(config),
                "loss_stages": [
                    {
                        "loss_mode": stage.get("loss_mode"),
                        "conditional_probability": stage.get("conditional_probability"),
                        "impact": stage.get("impact"),
                    }
                    for stage in (config.get("loss_stages") or [])
                ],
            })
        except Exception as exc:
            failures.append((scenario_path, exc))

    if not portfolio:
        raise ValueError("No valid simulations.")

    shard_stats, portfolio_stats, aggregate = compute_all_stats(portfolio)
    scenario_currencies = {
        item["name"]: item["currency"]
        for item in metadata["reproducibility"]["scenarios"]
    }
    unique_currencies = sorted(set(scenario_currencies.values()))
    known_unique_currencies = [
        currency for currency in unique_currencies
        if currency != "unspecified"
    ]
    metadata["currencies"] = {
        "scenarios": scenario_currencies,
        "unique": unique_currencies,
        "portfolio_currency": (
            known_unique_currencies[0]
            if len(known_unique_currencies) == 1 and "unspecified" not in unique_currencies
            else None
        ),
        "mixed_or_unspecified": len(unique_currencies) != 1 or "unspecified" in unique_currencies,
        "warning": None,
    }
    if metadata["currencies"]["mixed_or_unspecified"]:
        metadata["currencies"]["warning"] = (
            "Portfolio statistics are an unconverted arithmetic sum across "
            "mixed or unspecified scenario currencies."
        )
    return {
        "shards": shard_stats,
        "portfolio": portfolio_stats,
        "aggregate": aggregate,
        "failures": failures,
        "metadata": metadata,
    }


def plot_lec(results, name, output_dir=RESULTS_DIR):
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    sorted_results = sorted(results, reverse=True)
    probabilities = [i / len(sorted_results) for i in range(len(sorted_results))]

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_results, probabilities, linewidth=2)
    plt.fill_between(sorted_results, probabilities, alpha=0.1)
    plt.title(f"Loss Exceedance Curve: {name}")
    plt.xlabel("Loss")
    plt.ylabel("Exceedance Probability")
    plt.grid(True, linestyle="--", alpha=0.3)

    path = output_dir / f"lec_{name.replace(' ', '_')}.png"
    plt.savefig(path)
    plt.close()
    return path


def reproduction_command(path, trials, dist_type, seed):
    command = [
        "python",
        "scripts/fair_calc.py",
        str(path),
        "--trials",
        str(trials),
        "--dist",
        dist_type,
    ]
    if seed is not None:
        command.extend(["--seed", str(seed)])
    return " ".join(command)


def export_report(shard_stats, portfolio_stats, output_dir=RESULTS_DIR, timestamp=None, metadata=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = timestamp or datetime.now()
    filename = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    path = output_dir / filename

    caveats = [IMPACT_UNCERTAINTY_NOTE]
    if metadata is not None:
        scenarios = metadata.get("reproducibility", {}).get("scenarios", [])
        if any(scenario.get("loss_stages") for scenario in scenarios):
            caveats.append(LOSS_CHAIN_NOTE)

    payload = {
        "timestamp": timestamp.isoformat(),
        "shards": shard_stats,
        "portfolio": portfolio_stats,
        "caveats": caveats,
    }
    if metadata is not None:
        payload["metadata"] = metadata

    with open(path, "w") as f:
        json.dump(payload, f, indent=4)

    return path
