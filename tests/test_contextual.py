import json
import tempfile
import unittest
from pathlib import Path

from jsonschema.exceptions import ValidationError

from engine.contextual import run_contextual_analysis, write_contextual_report
from engine.profiles import load_org_profile, load_provenance


ROOT = Path(__file__).resolve().parents[1]


class ProfileValidationTests(unittest.TestCase):
    def test_org_profile_validates(self):
        profile = load_org_profile(ROOT / "org_profiles" / "au_finance_midmarket.yaml")

        self.assertEqual(profile["country"], "Australia")
        self.assertEqual(profile["industry"], "financial_services")

    def test_org_profile_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_org.yaml"
            path.write_text(
                "org_type: private_company\n"
                "industry: financial_services\n"
                "country: Australia\n"
                "employees: 100\n"
                "annual_revenue_or_budget: 10000000\n"
                "data_sensitivity: high\n"
                "internet_exposure: moderate\n"
                "third_party_dependency: high\n"
            )

            with self.assertRaises(ValidationError):
                load_org_profile(path)


class ProvenanceValidationTests(unittest.TestCase):
    def test_provenance_validates(self):
        provenance = load_provenance(
            ROOT / "provenance" / "au_finance_ransomware_midmarket.yaml"
        )

        self.assertEqual(provenance["records"][0]["evidence_type"], "synthetic")
        self.assertEqual(provenance["records"][0]["confidence"], "low")

    def test_provenance_rejects_unknown_evidence_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_provenance.yaml"
            path.write_text(
                "scenario_name: Bad\n"
                "records:\n"
                "  - parameter: frequency\n"
                "    source_name: Bad Source\n"
                "    source_type: placeholder\n"
                "    source_url_or_citation: none\n"
                "    publication_date: '2026-05-01'\n"
                "    extraction_date: '2026-05-01'\n"
                "    extraction_notes: test\n"
                "    applicability: test\n"
                "    confidence: low\n"
                "    evidence_type: guessed\n"
            )

            with self.assertRaises(ValidationError):
                load_provenance(path)


class ContextualAnalysisTests(unittest.TestCase):
    def test_contextual_run_includes_baseline_control_delta_and_provenance(self):
        report = run_contextual_analysis(
            ROOT / "scenarios" / "au_finance_ransomware_midmarket.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "control_profiles" / "ransomware_basic_controls.yaml",
            ROOT / "provenance" / "au_finance_ransomware_midmarket.yaml",
            trials=50,
            seed=7,
        )

        self.assertEqual(report["report_type"], "contextual_analysis")
        self.assertEqual(report["org_context"]["country"], "Australia")
        self.assertEqual(report["confidence"]["overall"], "low")
        self.assertEqual(
            report["source_provenance_summary"]["evidence_types"],
            ["synthetic"],
        )
        self.assertIn("baseline_results", report)
        self.assertIn("control_adjusted_results", report)
        self.assertLess(report["control_adjusted_results"]["p95"], report["baseline_results"]["p95"])
        self.assertLess(report["delta"]["p95_delta"], 0)

    def test_explainable_report_writer_outputs_json(self):
        report = run_contextual_analysis(
            ROOT / "scenarios" / "au_finance_ransomware_midmarket.yaml",
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
            ROOT / "control_profiles" / "ransomware_basic_controls.yaml",
            ROOT / "provenance" / "au_finance_ransomware_midmarket.yaml",
            trials=10,
            seed=3,
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_path = write_contextual_report(report, Path(tmp) / "report.json")
            payload = json.loads(output_path.read_text())

        self.assertEqual(payload["scenario"]["metadata"]["name"], "Australia Finance Ransomware Midmarket")
        self.assertEqual(payload["confidence"]["overall"], "low")
        self.assertIn("key_assumptions", payload)


if __name__ == "__main__":
    unittest.main()
