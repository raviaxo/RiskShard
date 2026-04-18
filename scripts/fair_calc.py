import yaml
import random
import statistics
import sys
import argparse
import json
from pathlib import Path
from jsonschema import validate, ValidationError

# Calculate project root based on this script's location
PROJECT_ROOT = Path(__file__).parent.parent

def load_schema():
    # Robust pathing: looks for schemas/shard_schema.json relative to project root
    schema_path = PROJECT_ROOT / 'schemas' / 'shard_schema.json'
    
    if not schema_path.exists():
        print(f"❌ Error: Schema not found at {schema_path}")
        print(f"   Make sure you created the 'schemas/' folder and 'shard_schema.json' file.")
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
        if dist_type == 'pert':
            f_sample = beta_pert(freq['min'], freq['likely'], freq['max'])
            i_sample = beta_pert(impact['min'], impact['likely'], impact['max'])
        else:
            f_sample = random.triangular(freq['min'], freq['likely'], freq['max'])
            i_sample = random.triangular(impact['min'], impact['likely'], impact['max'])
        results.append(f_sample * i_sample)

    return results, name

def display_portfolio_hud(portfolio_results, trials, dist_type):
    # Aggregate results by summing trials across all scenarios
    total_ale_results = [sum(x) for x in zip(*portfolio_results.values())]
    total_ale_results.sort()

    mean_ale = statistics.mean(total_ale_results)
    p50 = statistics.median(total_ale_results)
    p95 = total_ale_results[int(trials * 0.95)]
    p99 = total_ale_results[int(trials * 0.99)]
    
    print(f"\n\033[1;36m[ RISKSHARD PORTFOLIO v3.1 ]\033[0m")
    print(f"SHARDS LOADED: {len(portfolio_results)}")
    print(f"MATH:          {dist_type.upper()} (Validated)")
    print(f"TRIALS:        {trials:,}")
    print("-" * 50)
    
    for name in portfolio_results.keys():
        avg_scenario = statistics.mean(portfolio_results[name])
        print(f"  • {name[:25]:<25} | Avg ALE: ${avg_scenario:,.2f}")
    
    print("-" * 50)
    print(f"\033[1;35mAGGREGATE ANNUAL LOSS EXPECTANCY (ALE):\033[0m")
    print(f"  \033[1;32mAVG  >\033[0m ${mean_ale:,.2f}")
    print(f"  \033[1;32mP50  >\033[0m ${p50:,.2f}")
    print(f"  \033[1;33mP95  >\033[0m ${p95:,.2f} (Portfolio Tail)")
    print(f"  \033[1;31mP99  >\033[0m ${p99:,.2f} (Extreme Case)")
    print("-" * 50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RiskShard Quantitative Engine")
    parser.add_argument("path", help="Path to a YAML shard or a directory of shards")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=['triangular', 'pert'], default='pert')
    
    args = parser.parse_args()
    schema = load_schema()
    
    input_path = Path(args.path)
    portfolio = {}

    # Identify files to process
    if input_path.is_dir():
        files = list(input_path.glob('*.yaml'))
    else:
        files = [input_path]

    # Run simulations
    for f in files:
        res, name = run_simulation(f, args.trials, args.dist, schema)
        if res:
            portfolio[name] = res

    # Output report
    if portfolio:
        display_portfolio_hud(portfolio, args.trials, args.dist)
    else:
        print("❌ No valid shards found to simulate.")