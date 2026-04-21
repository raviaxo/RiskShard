import argparse
import json
import random
import statistics
from pathlib import Path
from datetime import datetime

import yaml
import matplotlib.pyplot as plt
from jsonschema import validate

# -----------------------------
# CONFIG
# -----------------------------
PROJECT_ROOT = Path(__file__).parent.parent

# -----------------------------
# UTILITIES
# -----------------------------

def load_schema():
    schema_path = PROJECT_ROOT / 'schemas' / 'shard_schema.json'
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)


def percentile(data, p):
    if not data:
        return 0
    k = int(len(data) * p)
    return data[min(k, len(data) - 1)]


def beta_pert(low, likely, high, confidence=4):
    if low >= high:
        return low
    a = 1 + confidence * (likely - low) / (high - low)
    b = 1 + confidence * (high - likely) / (high - low)
    return low + random.betavariate(a, b) * (high - low)

# -----------------------------
# CORE SIMULATION
# -----------------------------

def run_simulation(config, trials, dist_type):
    impact = config['impact']
    freq = config['frequency']
    name = config['metadata']['name']

    results = []
    for _ in range(trials):
        if dist_type == 'pert':
            f = beta_pert(freq['min'], freq['likely'], freq['max'])
            i = beta_pert(impact['min'], impact['likely'], impact['max'])
        else:
            f = random.triangular(freq['min'], freq['likely'], freq['max'])
            i = random.triangular(impact['min'], impact['likely'], impact['max'])

        results.append(f * i)

    return name, results


def load_and_validate(path, schema):
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    validate(instance=config, schema=schema)
    return config

# -----------------------------
# AGGREGATION
# -----------------------------

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

# -----------------------------
# OUTPUTS
# -----------------------------

def plot_lec(results, name):
    sorted_res = sorted(results, reverse=True)
    prob = [i / len(sorted_res) for i in range(len(sorted_res))]

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_res, prob, linewidth=2)
    plt.fill_between(sorted_res, prob, alpha=0.1)

    plt.title(f"Loss Exceedance Curve: {name}")
    plt.xlabel("Loss ($)")
    plt.ylabel("Exceedance Probability")
    plt.grid(True, linestyle='--', alpha=0.3)

    out = PROJECT_ROOT / f"results/lec_{name.replace(' ', '_')}.png"
    out.parent.mkdir(exist_ok=True)
    plt.savefig(out)
    print(f"📊 LEC saved: {out}")


def print_report(stats):
    print("\n=== PORTFOLIO RESULTS ===")
    print(f"AVG : ${stats['mean']:,.2f}")
    print(f"P50 : ${stats['p50']:,.2f}")
    print(f"P95 : ${stats['p95']:,.2f}")
    print(f"P99 : ${stats['p99']:,.2f}")


def export_report(stats):
    out_dir = PROJECT_ROOT / 'results'
    out_dir.mkdir(exist_ok=True)

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = out_dir / filename

    payload = {
        "timestamp": datetime.now().isoformat(),
        "aggregate": stats
    }

    with open(path, 'w') as f:
        json.dump(payload, f, indent=4)

    print(f"✅ Exported: {path}")

# -----------------------------
# MAIN
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="RiskShard Engine v4")
    parser.add_argument("path", help="Path to shard or directory")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=['triangular', 'pert'], default='pert')
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    schema = load_schema()
    input_path = Path(args.path)

    files = list(input_path.glob('*.yaml')) if input_path.is_dir() else [input_path]

    portfolio = {}

    for f in files:
        try:
            config = load_and_validate(f, schema)
            name, results = run_simulation(config, args.trials, args.dist)
            portfolio[name] = results
        except Exception as e:
            print(f"❌ Failed: {f} -> {e}")

    if not portfolio:
        print("No valid simulations.")
        return

    aggregate = aggregate_portfolio(portfolio)
    stats = compute_stats(aggregate)

    plot_lec(aggregate, "Portfolio")
    print_report(stats)

    if args.export:
        export_report(stats)


if __name__ == "__main__":
    main()
