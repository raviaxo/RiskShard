import json
import yaml
from pathlib import Path

# Paths relative to project root
BENCHMARK_FILE = Path('library/benchmarks/industry_stats.json')
OUTPUT_DIR = Path('scenarios')

def create_defensible_shard(industry, threat):
    if not BENCHMARK_FILE.exists():
        print(f"❌ Error: {BENCHMARK_FILE} not found.")
        return

    with open(BENCHMARK_FILE, 'r') as f:
        data = json.load(f)

    if industry not in data or threat not in data[industry]:
        print(f"❌ Error: No benchmark found for {industry}/{threat}")
        return

    stats = data[industry][threat]

    # Standardized naming for your CLI commands
    file_name = f"{industry}_{threat}_v1.yaml"

    shard = {
        "metadata": {
            "name": f"{industry.upper()} - {threat.replace('_', ' ').title()}",
            "version": "1.0",
            "source": stats['source']
        },
        "frequency": {
            "min": round(stats['freq_likely'] * 0.5, 3),
            "likely": stats['freq_likely'],
            "max": round(stats['freq_likely'] * 3.0, 3) 
        },
        "impact": {
            "min": int(stats['impact_median'] * 0.2),
            "likely": int(stats['impact_median']),
            "max": int(stats['impact_p95'])
        }
    }

    with open(OUTPUT_DIR / file_name, 'w') as f:
        yaml.dump(shard, f, sort_keys=False)

    print(f"✅ Defensible Shard created: scenarios/{file_name}")

if __name__ == "__main__":
    create_defensible_shard("finance", "ransomware")