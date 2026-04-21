import json
import yaml
from pathlib import Path

def create_shard(industry, threat, output_path):
    # Load our "Universal Truth" benchmarks
    with open('library/benchmarks/industry_stats.json', 'r') as f:
        benchmarks = json.load(f)
    
    stats = benchmarks[industry][threat]
    
    # Mathematical Bridge to PERT
    # Frequency: Likely = Benchmark. Min/Max = 50% variance for "Team of One" defensibility.
    shard = {
        "metadata": {
            "name": f"{industry.title()} {threat.title()} Shard",
            "version": "1.0",
            "source": stats['source']
        },
        "frequency": {
            "min": stats['freq_likely'] * 0.5,
            "likely": stats['freq_likely'],
            "max": stats['freq_likely'] * 2.0
        },
        "impact": {
            "min": stats['impact_median'] * 0.1, # Typical low-end
            "likely": stats['impact_median'],
            "max": stats['impact_p95']         # Defensible high-end
        }
    }

    with open(output_path, 'w') as f:
        yaml.dump(shard, f, sort_keys=False)
    print(f"✅ Generated defensible shard: {output_path}")

if __name__ == "__main__":
    create_shard("finance", "ransomware", "scenarios/fin_ransomware_v1.yaml")