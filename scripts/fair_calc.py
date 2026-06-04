import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.fair_calc import export_report, plot_lec, run_portfolio


def format_money(value, currency=None):
    if currency and currency != "unspecified":
        return f"{currency} {value:,.2f}"
    return f"${value:,.2f}"


def portfolio_currency_text(metadata):
    currencies = (metadata or {}).get("currencies", {})
    portfolio_currency = currencies.get("portfolio_currency")
    if portfolio_currency:
        return portfolio_currency
    return "unconverted mixed/unspecified currencies"


def build_parser():
    parser = argparse.ArgumentParser(description="RiskShard CLI")
    parser.add_argument("path", help="Path to a scenario YAML file or directory")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=["triangular", "pert"], default="pert")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    return parser


def print_full_report(shard_stats, portfolio_stats, metadata=None):
    scenario_meta = {
        item["name"]: item
        for item in (metadata or {}).get("reproducibility", {}).get("scenarios", [])
    }
    currency_warning = (metadata or {}).get("currencies", {}).get("warning")
    print("\n=== SHARD RESULTS ===")

    for name, stats in shard_stats.items():
        meta = scenario_meta.get(name, {})
        stage = meta.get("stage_label", "unknown stage")
        currency = meta.get("currency")
        print(f"\n{name}")
        print(f"  STAGE: {stage}")
        print(f"  AVG : {format_money(stats['mean'], currency)}")
        print(f"  P95 : {format_money(stats['p95'], currency)}")

    print(f"\n=== PORTFOLIO ({portfolio_currency_text(metadata)}) ===")
    if currency_warning:
        print(f"WARNING: {currency_warning}")
    print(f"AVG : {format_money(portfolio_stats['mean'], (metadata or {}).get('currencies', {}).get('portfolio_currency'))}")
    print(f"P95 : {format_money(portfolio_stats['p95'], (metadata or {}).get('currencies', {}).get('portfolio_currency'))}")
    print(f"P99 : {format_money(portfolio_stats['p99'], (metadata or {}).get('currencies', {}).get('portfolio_currency'))}")


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

    print_full_report(run["shards"], run["portfolio"], run["metadata"])

    if args.export:
        report_path = export_report(run["shards"], run["portfolio"], metadata=run["metadata"])
        print(f"Exported: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
