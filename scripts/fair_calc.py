import random
import yaml
import os

def run_simulation(min_val, max_val, likely_val, iterations=10000):
    results = [random.triangular(min_val, max_val, likely_val) for _ in range(iterations)]
    return sum(results) / len(results)

# 1. Open the real YAML file
file_path = "scenarios/saas_ransomware.yaml"

if os.path.exists(file_path):
    with open(file_path, "r") as file:
        shard_data = yaml.safe_load(file) # This reads the YAML!
    
    # 2. Run the math
    avg = run_simulation(shard_data['min'], shard_data['max'], shard_data['likely'])

    print(f"--- RiskShard Phase 2 Active ---")
    print(f"Scenario: {shard_data['title']}")
    print(f"Average Impact: ${avg:,.2f}")
else:
    print(f"Error: Could not find the file at {file_path}")