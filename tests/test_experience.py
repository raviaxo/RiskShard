import unittest
from pathlib import Path

from engine.experience import analyze_gaps, format_gap_analysis, format_top_risks, rank_top_risks


ROOT = Path(__file__).resolve().parents[1]
ORG_PROFILE = ROOT / "org_profiles" / "au_finance_midmarket.yaml"


class ExperienceTests(unittest.TestCase):
    def test_gap_analysis_explains_ready_and_assumption_parameters(self):
        analysis = analyze_gaps(ORG_PROFILE, "data_breach")
        output = format_gap_analysis(analysis)

        self.assertEqual(analysis["threat"], "data_breach")
        self.assertEqual(len(analysis["direct_parameters"]), 6)
        self.assertEqual(analysis["assumption_parameters"], [])
        self.assertNotIn("impact.min", analysis["assumption_parameters"])
        self.assertEqual(analysis["source_warnings"], [])
        self.assertIn("Gap analysis: data_breach", output)
        self.assertIn("ready for calibrated run", output)

    def test_top_risks_show_calibrated_and_partially_supported_threats(self):
        rows = rank_top_risks(ORG_PROFILE)
        by_id = {row["id"]: row for row in rows}
        output = format_top_risks(rows)

        self.assertEqual(by_id["data_breach"]["status"], "calibrated")
        self.assertEqual(by_id["ransomware"]["status"], "calibrated")
        self.assertEqual(by_id["business_email_compromise"]["status"], "calibrated")
        self.assertEqual(by_id["ai_enabled_fraud"]["status"], "calibrated")
        self.assertTrue(by_id["ai_enabled_fraud"]["calibration_profile_exists"])
        self.assertEqual(by_id["ai_enabled_fraud"]["assumption_parameters"], 0)
        self.assertEqual(by_id["insider_misuse"]["status"], "calibrated")
        self.assertTrue(by_id["insider_misuse"]["calibration_profile_exists"])
        self.assertEqual(by_id["insider_misuse"]["assumption_parameters"], 0)
        self.assertEqual(by_id["third_party_outage"]["status"], "calibrated_with_assumptions")
        self.assertTrue(by_id["third_party_outage"]["calibration_profile_exists"])
        self.assertEqual(by_id["third_party_outage"]["assumption_parameters"], 1)
        self.assertEqual(by_id["data_breach"]["direct_coverage"], 6)
        self.assertTrue(by_id["data_breach"]["calibration_profile_exists"])
        self.assertEqual(by_id["data_breach"]["assumption_parameters"], 0)
        self.assertEqual(by_id["ransomware"]["assumption_parameters"], 0)
        self.assertTrue(by_id["business_email_compromise"]["calibration_profile_exists"])
        self.assertEqual(by_id["business_email_compromise"]["assumption_parameters"], 0)
        self.assertEqual(rows[0]["id"], "business_email_compromise")
        self.assertEqual(rows[1]["id"], "data_breach")
        self.assertEqual(rows[2]["id"], "ransomware")
        self.assertIn("Top risks", output)
        self.assertIn("Data Breach", output)


if __name__ == "__main__":
    unittest.main()
