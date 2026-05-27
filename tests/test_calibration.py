import json
import tempfile
import unittest
from pathlib import Path

from engine.calibration import (
    run_calibration,
    write_calibrated_scenario,
    write_calibration_report,
)
from engine.fair_calc import load_and_validate


ROOT = Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def test_calibration_generates_scenario_ranges_from_selected_evidence(self):
        report = run_calibration(
            ROOT / "scenarios" / "au_finance_ransomware_midmarket.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "au_finance_ransomware.yaml",
            threat="ransomware",
        )

        scenario = report["generated_scenario"]

        self.assertEqual(scenario["frequency"], {"min": 0.1, "likely": 0.65, "max": 0.85})
        self.assertEqual(scenario["impact"]["min"], 100000)
        self.assertEqual(scenario["impact"]["likely"], 3870000)
        self.assertEqual(scenario["impact"]["max"], 9000000)
        self.assertIn(
            "parameter_from_non_source_backed_evidence",
            {warning["code"] for warning in report["warnings"]},
        )
        self.assertEqual(
            report["assumptions"][0]["rate_id"],
            "usd_to_aud_planning_2026_05_26",
        )

    def test_calibration_report_and_scenario_outputs_are_loadable(self):
        report = run_calibration(
            ROOT / "scenarios" / "au_finance_ransomware_midmarket.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "au_finance_ransomware.yaml",
            threat="ransomware",
        )

        with tempfile.TemporaryDirectory() as tmp:
            report_path = write_calibration_report(report, Path(tmp) / "calibration.json")
            scenario_path = write_calibrated_scenario(report, Path(tmp) / "scenario.yaml")

            payload = json.loads(report_path.read_text())
            scenario = load_and_validate(scenario_path)

        self.assertEqual(payload["report_type"], "scenario_calibration")
        self.assertEqual(
            scenario["metadata"]["name"],
            "Australia Finance Ransomware Midmarket - Calibrated Draft",
        )


if __name__ == "__main__":
    unittest.main()
