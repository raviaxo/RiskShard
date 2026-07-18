#!/usr/bin/env python3
"""Backtest a shard's frequency model against VCDB open incident data.

Roadmap Lane 2, S1 (frequency-only PoC). See docs/S1_BACKTEST_POC_PLAN.md.
"""
import argparse
import json
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.backtesting import (  # noqa: E402
    build_frequency_backtest_report,
    format_frequency_backtest_report,
    load_vcdb_records,
)
from engine.scenarios import load_scenario  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Frequency backtest against VCDB.")
    parser.add_argument("--scenario", default="scenarios/gb_finance_data_breach_midmarket.yaml",
                        help="Shard scenario whose frequency band is tested (primary cell).")
    parser.add_argument("--primary-country", default="GB")
    parser.add_argument("--secondary-country", default="US")
    parser.add_argument("--since-year", type=int, default=2015)
    parser.add_argument("--firms", type=int, default=None,
                        help="Explicit firm-count denominator for a per-firm rate check (labeled assumption).")
    parser.add_argument("--no-download", action="store_true",
                        help="Fail if the VCDB cache is missing instead of downloading.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    scenario = load_scenario(ROOT / args.scenario)
    shard_id = Path(args.scenario).stem
    shard_frequency = scenario["frequency"]

    records, provenance = load_vcdb_records(allow_download=not args.no_download)
    report = build_frequency_backtest_report(
        records,
        provenance,
        shard_id=shard_id,
        shard_frequency=shard_frequency,
        primary_country=args.primary_country,
        secondary_country=args.secondary_country,
        since_year=args.since_year,
        firms=args.firms,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_frequency_backtest_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
