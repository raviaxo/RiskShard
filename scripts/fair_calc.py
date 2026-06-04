import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.fair_calc import export_report, plot_lec, run_portfolio


def build_parser():
    parser = argparse.ArgumentParser(description="RiskShard CLI")
    parser.add_argument("path", help="Path to a scenario YAML file or directory")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=["triangular", "pert"], default="pert")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    return parser


def print_full_report(shard_stats, portfolio_stats):
    print("\n=== SHARD RESULTS ===")

    for name, stats in shard_stats.items():
        print(f"\n{name}")
        print(f"  AVG : ${stats['mean']:,.2f}")
        print(f"  P95 : ${stats['p95']:,.2f}")

    print("\n=== PORTFOLIO ===")
    print(f"AVG : ${portfolio_stats['mean']:,.2f}")
    print(f"P95 : ${portfolio_stats['p95']:,.2f}")
    print(f"P99 : ${portfolio_stats['p99']:,.2f}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        run = run_portfolio(
            args.path,
            trials=args.trials,
            dist_type=args.dist,
            seed=args.seed,
        )
    except Exception as exc:
        print(f"RiskShard failed: {exc}", file=sys.stderr)
        return 1

    for path, exc in run["failures"]:
        print(f"Failed: {path} -> {exc}", file=sys.stderr)

    lec_path = plot_lec(run["aggregate"], "Portfolio")
    print(f"LEC saved: {lec_path}")

    print_full_report(run["shards"], run["portfolio"])

    if args.export:
        report_path = export_report(run["shards"], run["portfolio"], metadata=run["metadata"])
        print(f"Exported: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
