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

        self.assertEqual(scenario["frequency"], {"min": 0.1, "likely": 0.54, "max": 0.7})
        self.assertEqual(scenario["impact"]["min"], 97000)
        self.assertEqual(scenario["impact"]["likely"], 2310000)
        self.assertEqual(scenario["impact"]["max"], 76000000)
        self.assertEqual(report["warnings"], [])
        selected_by_id = {
            item["evidence_id"]: item
            for item in report["selected_evidence"]
        }
        self.assertTrue(
            selected_by_id["sophos_2024_au_ransomware_attack_rate_likely"]["selection"][
                "best_available_for_parameter"
            ]
        )
        # After the 2026-08-02 rework every selected anchor is the best available
        # for its parameter (the superseded legacy estimated records are gone).
        self.assertTrue(
            selected_by_id["cyentia_global_ransomware_probability_2025"]["selection"][
                "best_available_for_parameter"
            ]
        )
        self.assertEqual(
            selected_by_id["cyentia_global_ransomware_probability_2025"]["selection"][
                "higher_scored_alternatives"
            ],
            [],
        )
        # One FX assumption remains: the Sophos Australia recovery cost is USD.
        self.assertEqual(len(report["assumptions"]), 1)
        self.assertEqual(
            report["assumptions"][0]["rate_id"],
            "inverse:aud_to_usd_rba_f11_1_2026_06_01",
        )
        self.assertEqual(report["assumptions"][0]["evidence_type"], "source_backed")
        self.assertEqual(report["assumptions"][0]["retrieved_at"], "2026-06-01")
        self.assertIn("F11.1 Exchange Rates", report["assumptions"][0]["citation_detail"])
        self.assertEqual(
            report["assumptions"][0]["evidence_id"],
            "sophos_au_2026_ransomware_recovery_cost_usd",
        )

    def test_calibration_generates_loss_stages_from_profile(self):
        report = run_calibration(
            ROOT / "scenarios" / "data_breach.yaml",
            ROOT / "org_profiles" / "gb_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "gb_finance_data_breach_regulatory_chain.yaml",
            threat="data_breach",
        )
        scenario = report["generated_scenario"]

        self.assertIn("loss_stages", scenario)
        stage = scenario["loss_stages"][0]
        self.assertEqual(stage["loss_mode"], "regulatory_penalty")
        self.assertEqual(
            stage["conditional_probability"],
            {"min": 0.001, "likely": 0.0015, "max": 0.005},
        )
        self.assertEqual(
            stage["impact"],
            {"min": 50000, "likely": 150000, "max": 12700000},
        )
        # The conditional-probability min/max are labeled estimates and surface as warnings.
        estimated = {
            warning["parameter"]
            for warning in report["warnings"]
            if warning["code"] == "parameter_from_non_source_backed_evidence"
        }
        self.assertIn("loss_stage.regulatory_penalty.conditional_probability.min", estimated)
        self.assertIn("loss_stage.regulatory_penalty.conditional_probability.max", estimated)

    def test_loss_stage_inverted_range_is_rejected(self):
        from engine.calibration import validate_generated_loss_stages, CalibrationError

        inverted_probability = {
            "loss_stages": [
                {
                    "loss_mode": "regulatory_penalty",
                    "conditional_probability": {"min": 0.9, "likely": 0.1, "max": 0.2},
                    "impact": {"min": 1, "likely": 2, "max": 3},
                }
            ]
        }
        inverted_impact = {
            "loss_stages": [
                {
                    "loss_mode": "regulatory_penalty",
                    "conditional_probability": {"min": 0.1, "likely": 0.2, "max": 0.3},
                    "impact": {"min": 5000, "likely": 2000, "max": 1000},
                }
            ]
        }
        with self.assertRaises(CalibrationError):
            validate_generated_loss_stages(inverted_probability)
        with self.assertRaises(CalibrationError):
            validate_generated_loss_stages(inverted_impact)

    def test_calibration_markdown_includes_loss_stage_rows(self):
        from engine.calibration import format_calibration_markdown

        report = run_calibration(
            ROOT / "scenarios" / "data_breach.yaml",
            ROOT / "org_profiles" / "gb_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "gb_finance_data_breach_regulatory_chain.yaml",
            threat="data_breach",
        )
        markdown = format_calibration_markdown(report)
        self.assertIn("loss_stage[regulatory_penalty].conditional_probability", markdown)
        self.assertIn("loss_stage[regulatory_penalty].impact", markdown)

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
        # "Higher-scored alternatives:" no longer appears for this shard - every
        # selected anchor is best-available after the 2026-08-02 rework.
        self.assertIn("Best available for parameter:", markdown)

    def test_data_breach_calibration_is_runnable_with_frequency_bridges(self):
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

        self.assertEqual(scenario["frequency"], {"min": 0.0008, "likely": 0.65, "max": 0.69})
        self.assertEqual(scenario["impact"], {"min": 97000, "likely": 6300000, "max": 50000000})
        self.assertEqual(
            warning_codes.count("parameter_from_non_source_backed_evidence"),
            0,
        )
        self.assertEqual(
            selected_types,
            {
                "frequency.min": "source_backed",
                "frequency.likely": "source_backed",
                "frequency.max": "source_backed",
                "impact.min": "source_backed",
                "impact.likely": "source_backed",
                "impact.max": "source_backed",
            },
        )
        # After the 2026-08-02 move to IBM's Australian financial-services cell
        # (already AUD), this calibration carries no FX assumptions at all.
        self.assertEqual(set(assumptions_by_evidence), set())
        self.assertIn(
            "verizon_dbir_2026_vulnerability_exploitation_breach_entry_share",
            {item["id"] for item in report["excluded_evidence"]},
        )

    def test_bec_calibration_is_runnable_and_source_backed(self):
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

        self.assertEqual(
            scenario["frequency"],
            {"min": 0.00010514176186819692, "likely": 0.21, "max": 0.81},
        )
        self.assertEqual(scenario["impact"], {"min": 33000, "likely": 170000, "max": 2670000})
        self.assertEqual(
            warning_codes.count("parameter_from_non_source_backed_evidence"),
            0,
        )
        self.assertEqual(
            selected_types,
            {
                "frequency.min": "source_backed",
                "frequency.likely": "source_backed",
                "frequency.max": "source_backed",
                "impact.min": "source_backed",
                "impact.likely": "source_backed",
                "impact.max": "source_backed",
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
        self.assertEqual(
            report["selected_evidence"][5]["evidence_id"],
            "afp_2020_au_bec_documented_single_event_loss_aud",
        )

    def test_gb_data_breach_calibration_uses_source_backed_direct_parameters(self):
        report = run_calibration(
            ROOT / "scenarios" / "gb_finance_data_breach_midmarket.yaml",
            ROOT / "org_profiles" / "gb_finance_midmarket.yaml",
            ROOT / "evidence",
            ROOT / "calibrations" / "gb_finance_data_breach.yaml",
            threat="data_breach",
        )

        scenario = report["generated_scenario"]
        selected_types = {
            item["parameter"]: item["evidence_type"]
            for item in report["selected_evidence"]
        }

        self.assertEqual(scenario["frequency"], {"min": 0.43, "likely": 0.65, "max": 0.69})
        self.assertEqual(scenario["impact"], {"min": 10000, "likely": 5740000, "max": 11164400})
        self.assertEqual(
            selected_types,
            {
                "frequency.min": "source_backed",
                "frequency.likely": "source_backed",
                "frequency.max": "source_backed",
                "impact.min": "source_backed",
                "impact.likely": "source_backed",
                "impact.max": "source_backed",
            },
        )
        selected_by_parameter = {
            item["parameter"]: item
            for item in report["selected_evidence"]
        }
        self.assertEqual(
            selected_by_parameter["impact.max"]["evidence_id"],
            "fca_equifax_2023_cyber_breach_fine_gbp",
        )
        self.assertEqual(
            [warning["code"] for warning in report["warnings"]].count("parameter_from_non_source_backed_evidence"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
