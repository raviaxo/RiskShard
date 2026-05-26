import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.contextual import run_contextual_analysis, write_contextual_report
from engine.fair_calc import export_report, plot_lec, run_portfolio


def build_parser():
    parser = argparse.ArgumentParser(description="RiskShard CLI")
    parser.add_argument("path", help="Path to a scenario YAML file or directory")
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--dist", choices=["triangular", "pert"], default="pert")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--org-profile", help="Organization profile YAML for contextual analysis")
    parser.add_argument("--control-profile", help="Control profile YAML for contextual analysis")
    parser.add_argument("--provenance", help="Provenance YAML for contextual analysis")
    parser.add_argument("--threat", help="Canonical threat id or alias for evidence matching")
    parser.add_argument("--evidence", help="Evidence YAML file or directory for evidence matching")
    parser.add_argument("--report-output", help="Path for contextual JSON report output")
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

    contextual_args = [args.org_profile, args.control_profile, args.provenance]
    if any(contextual_args):
        if not all(contextual_args):
            parser.error("--org-profile, --control-profile, and --provenance must be provided together")

        try:
            report = run_contextual_analysis(
                args.path,
                args.org_profile,
                args.control_profile,
                args.provenance,
                trials=args.trials,
                dist_type=args.dist,
                seed=args.seed,
                threat=args.threat,
                evidence_path=args.evidence,
            )
            report_path = write_contextual_report(report, args.report_output)
        except Exception as exc:
            print(f"RiskShard contextual analysis failed: {exc}", file=sys.stderr)
            return 1

        print(f"Contextual report saved: {report_path}")
        print("\n=== CONTEXTUAL ANALYSIS ===")
        print(f"Scenario : {report['scenario']['metadata'].get('name', args.path)}")
        print(f"Org      : {report['org_context'].get('metadata', {}).get('name', 'Unnamed org')}")
        print(f"Confidence: {report['confidence']['overall']}")
        if report.get("evidence_match"):
            match = report["evidence_match"]
            print(f"Evidence matches: {match['match_count']}")
            print(f"Evidence context: {match['target_context']}")
        print("\n=== BASELINE ===")
        print(f"AVG : ${report['baseline_results']['mean']:,.2f}")
        print(f"P95 : ${report['baseline_results']['p95']:,.2f}")
        print("\n=== CONTROL ADJUSTED ===")
        print(f"AVG : ${report['control_adjusted_results']['mean']:,.2f}")
        print(f"P95 : ${report['control_adjusted_results']['p95']:,.2f}")
        print("\n=== DELTA ===")
        print(f"Mean Delta : ${report['delta']['mean_delta']:,.2f}")
        print(f"P95 Delta  : ${report['delta']['p95_delta']:,.2f}")
        print(f"P95 Reduction: {report['delta']['reduction_pct_p95']:.1%}")
        return 0

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
        report_path = export_report(run["shards"], run["portfolio"])
        print(f"Exported: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
