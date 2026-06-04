import json
import tempfile
import unittest
from pathlib import Path

from engine.calibration import (
    run_calibration,
    write_calibrated_scenario,
    write_calibration_markdown_report,
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
        self.assertEqual(scenario["impact"]["min"], 97000)
        self.assertEqual(scenario["impact"]["likely"], 3590000)
        self.assertEqual(scenario["impact"]["max"], 9000000)
        self.assertIn(
            "parameter_from_non_source_backed_evidence",
            {warning["code"] for warning in report["warnings"]},
        )
        selected_by_id = {
            item["evidence_id"]: item
            for item in report["selected_evidence"]
        }
        self.assertTrue(
            selected_by_id["sophos_fin_services_ransomware_frequency_2024"]["selection"][
                "best_available_for_parameter"
            ]
        )
        self.assertFalse(
            selected_by_id["cyentia_global_ransomware_probability_2025"]["selection"][
                "best_available_for_parameter"
            ]
        )
        self.assertEqual(
            selected_by_id["cyentia_global_ransomware_probability_2025"]["selection"][
                "higher_scored_alternatives"
            ][0]["id"],
            "riskshard_au_sme_cybercrime_frequency_floor_2026",
        )
        self.assertEqual(
            report["assumptions"][0]["rate_id"],
            "inverse:aud_to_usd_rba_f11_1_2026_06_01",
        )
        self.assertEqual(report["assumptions"][0]["evidence_type"], "source_backed")
        self.assertEqual(report["assumptions"][0]["retrieved_at"], "2026-06-01")
        self.assertIn("F11.1 Exchange Rates", report["assumptions"][0]["citation_detail"])

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
            markdown_path = write_calibration_markdown_report(report, Path(tmp) / "calibration.md")
            scenario_path = write_calibrated_scenario(report, Path(tmp) / "scenario.yaml")

            payload = json.loads(report_path.read_text())
            markdown = markdown_path.read_text()
            scenario = load_and_validate(scenario_path)

        self.assertEqual(payload["report_type"], "scenario_calibration")
        self.assertEqual(
            scenario["metadata"]["name"],
            "Australia Finance Ransomware Midmarket - Calibrated Draft",
        )
        self.assertIn("# Calibration Report:", markdown)
        self.assertIn("## Bottom Line", markdown)
        self.assertIn("## Confidence", markdown)
        self.assertIn("## What Changed From Base Scenario", markdown)
        self.assertIn("## Limitations Summary", markdown)
        self.assertIn("## Generated Scenario", markdown)
        self.assertIn("## Selected Evidence", markdown)
        self.assertIn("## Excluded Evidence", markdown)
        self.assertIn("## Assumptions", markdown)
        self.assertIn("## Warnings", markdown)
        self.assertIn("## Quality Issues", markdown)
        self.assertIn("Reserve Bank of Australia Statistical Table F11.1", markdown)
        self.assertIn("Higher-scored alternatives:", markdown)
        self.assertIn("Best available for parameter:", markdown)

    def test_data_breach_calibration_is_runnable_but_assumption_backed(self):
        report = run_calibration(
            ROOT / "scenarios" / "data_breach.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "au_finance_data_breach.yaml",
            threat="data_breach",
        )

        scenario = report["generated_scenario"]
        warning_codes = [warning["code"] for warning in report["warnings"]]
        selected_types = {
            item["parameter"]: item["evidence_type"]
            for item in report["selected_evidence"]
        }
        assumptions_by_evidence = {
            item["evidence_id"]: item
            for item in report["assumptions"]
        }

        self.assertEqual(scenario["frequency"], {"min": 0.0008, "likely": 0.18, "max": 0.35})
        self.assertEqual(scenario["impact"], {"min": 370000, "likely": 6100000, "max": 44500000})
        self.assertEqual(
            warning_codes.count("parameter_from_non_source_backed_evidence"),
            2,
        )
        self.assertEqual(
            selected_types,
            {
                "frequency.min": "source_backed",
                "frequency.likely": "estimated",
                "frequency.max": "estimated",
                "impact.min": "source_backed",
                "impact.likely": "source_backed",
                "impact.max": "source_backed",
            },
        )
        self.assertEqual(
            set(assumptions_by_evidence),
            {
                "cyentia_iris_2022_typical_cyber_event_loss_usd",
                "ibm_cost_data_breach_2025_global_average_cost_usd",
                "cyentia_iris_2025_extreme_security_incident_loss_usd",
            },
        )
        self.assertEqual(
            {item["rate_id"] for item in assumptions_by_evidence.values()},
            {"inverse:aud_to_usd_rba_f11_1_2026_06_01"},
        )
        self.assertIn(
            "verizon_dbir_2026_vulnerability_exploitation_breach_entry_share",
            {item["id"] for item in report["excluded_evidence"]},
        )

    def test_bec_calibration_is_runnable_but_assumption_backed(self):
        report = run_calibration(
            ROOT / "scenarios" / "business_email_compromise.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "au_finance_business_email_compromise.yaml",
            threat="business_email_compromise",
        )

        scenario = report["generated_scenario"]
        warning_codes = [warning["code"] for warning in report["warnings"]]
        selected_types = {
            item["parameter"]: item["evidence_type"]
            for item in report["selected_evidence"]
        }

        self.assertEqual(scenario["frequency"], {"min": 0.04, "likely": 0.12, "max": 0.25})
        self.assertEqual(scenario["impact"], {"min": 25000, "likely": 170000, "max": 1500000})
        self.assertEqual(
            warning_codes.count("parameter_from_non_source_backed_evidence"),
            5,
        )
        self.assertEqual(
            selected_types,
            {
                "frequency.min": "estimated",
                "frequency.likely": "estimated",
                "frequency.max": "estimated",
                "impact.min": "estimated",
                "impact.likely": "source_backed",
                "impact.max": "estimated",
            },
        )
        self.assertEqual(
            report["assumptions"][0]["rate_id"],
            "inverse:aud_to_usd_rba_f11_1_2026_06_01",
        )
        self.assertEqual(
            report["selected_evidence"][4]["evidence_id"],
            "fbi_ic3_2025_bec_average_loss_per_complaint_usd",
        )
        self.assertIn(
            "accc_2025_small_business_false_billing_losses_aud",
            {item["id"] for item in report["excluded_evidence"]},
        )


if __name__ == "__main__":
    unittest.main()
