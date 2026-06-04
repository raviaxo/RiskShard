#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.calibration import (  # noqa: E402
    run_calibration,
    write_calibrated_scenario,
    write_calibration_markdown_report,
    write_calibration_report,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Calibrate a scenario from reviewed evidence.")
    parser.add_argument("scenario", type=Path, help="Base scenario YAML file.")
    parser.add_argument("--org-profile", required=True, type=Path)
    parser.add_argument("--evidence", default=ROOT / "evidence", type=Path)
    parser.add_argument("--calibration", required=True, type=Path)
    parser.add_argument("--threat", required=True)
    parser.add_argument("--manifest", default=ROOT / "sources" / "manifest.json", type=Path)
    parser.add_argument("--fx-rates", default=ROOT / "calibrations" / "fx_rates.yaml", type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--scenario-output", type=Path)
    return parser.parse_args()


def main(argv=None):
    args = parse_args()

    try:
        report = run_calibration(
            args.scenario,
            args.org_profile,
            args.evidence,
            args.calibration,
            threat=args.threat,
            manifest_path=args.manifest,
            fx_rates_path=args.fx_rates,
        )
        report_path = write_calibration_report(report, args.report_output)
        markdown_path = None
        if args.markdown_output:
            markdown_path = write_calibration_markdown_report(report, args.markdown_output)
        scenario_path = None
        if args.scenario_output:
            scenario_path = write_calibrated_scenario(report, args.scenario_output)
    except Exception as exc:
        print(f"RiskShard calibration failed: {exc}", file=sys.stderr)
        return 1

    print(f"Calibration report saved: {report_path}")
    if markdown_path:
        print(f"Markdown report saved: {markdown_path}")
    if scenario_path:
        print(f"Calibrated scenario saved: {scenario_path}")

    generated = report["generated_scenario"]
    print("\n=== CALIBRATED SCENARIO ===")
    print(f"Scenario : {generated['metadata']['name']}")
    print(f"Frequency: {generated['frequency']}")
    print(f"Impact   : {generated['impact']}")
    print(f"Warnings : {len(report['warnings'])}")
    print(f"Quality issues: {len(report['quality_issues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
