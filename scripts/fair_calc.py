import yaml
import random
import statistics
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent

def load_schema():
    schema_path = PROJECT_ROOT / 'schemas' / 'shard_schema.json'
    if not schema_path.exists():
        print(f"❌ Error: Schema not found at {schema_path}")
        sys.exit(1)
    with open(schema_path, 'r') as f:
        return json.load(f)

def beta_pert(low, likely, high, confidence=4):
    if low >= high: return low
    a = 1 + confidence * (likely - low) / (high - low)
    b = 1 + confidence * (high - likely) / (high - low)
    return low + random.betavariate(a, b) * (high - low)

def run_simulation(scenario_path, trials=10000, dist_type='pert', schema=None):
    try:
        with open(scenario_path, 'r') as f:
            config = yaml.safe_load(f)
        validate(instance=config, schema=schema)
    except Exception as e:
        print(f"❌ Error in shard '{scenario_path}': {e}")
        return None, None

    impact = config['impact']
    freq = config['frequency']
    name = config['metadata']['name']
    
    results = []
    for _ in range(trials):
        f_sample = beta_pert(freq['min'], freq['likely'], freq['max']) if dist_type == 'pert' else random.triangular(freq['min'], freq['likely'], freq['max'])
        i_sample = beta_pert(impact['min'], impact['likely'], impact['max']) if dist_type == 'pert' else random.triangular(impact['min'], impact['likely'], impact['max'])
        results.append(f_sample * i_sample)

    return results, name

def display_and_export(portfolio_results, trials, dist_type, export_json=False):
    total_ale_results = [sum(x) for x in zip(*portfolio_results.values())]
    total_ale_results.sort()

    stats = {
        "timestamp": datetime.now().isoformat(),
        "trials": trials,
        "distribution": dist_type,
        "shards": {name: {"avg_ale": statistics.mean(res)} for name, res in portfolio_results.items()},
        "aggregate": {
            "mean": statistics.mean(total_ale_results),
            "p50": statistics.median(total_ale_results),
            "p95": total_ale_results[int(trials * 0.95)],
            "p99": total_ale_results[int(trials * 0.99)]
        }
    }

    print(f"\n\033[1;36m[ RISKSHARD PORTFOLIO v3.2 ]\033[0m")
    print(f"AGGREGATE ALE:")
    print(f"  \033[1;32mAVG  >\033[0m ${stats['aggregate']['mean']:,.2f}")
    print(f"  \033[1;33mP95  >\033[0m ${stats['aggregate']['p95']:,.2f}")

    if export_json:
        export_dir = PROJECT_ROOT / 'results'
        export_dir.mkdir(exist_ok=True)
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_dir / filename, 'w') as f:
            json.dump(stats, f, indent=4)
        print(f"\n✅ Exported: results/{filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RiskShard Quantitative Engine")
    parser.add_argument("path", help="Path to shard or directory")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=['triangular', 'pert'], default='pert')
    parser.add_argument("--export", action="store_true", help="Export results to JSON")
    
    args = parser.parse_args()
    schema = load_schema()
    input_path = Path(args.path)
    portfolio = {}

    files = list(input_path.glob('*.yaml')) if input_path.is_dir() else [input_path]
    for f in files:
        res, name = run_simulation(f, args.trials, args.dist, schema)
        if res: portfolio[name] = res

    if portfolio:
        display_and_export(portfolio, args.trials, args.dist, args.export)