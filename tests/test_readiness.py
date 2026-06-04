import unittest
from pathlib import Path

from engine.readiness import build_readiness_dashboard, format_readiness_dashboard


ROOT = Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    def test_readiness_dashboard_summarizes_global_layers(self):
        dashboard = build_readiness_dashboard(
            ROOT,
            ROOT / "org_profiles" / "au_finance_midmarket.yaml",
        )

        self.assertGreaterEqual(dashboard["coverage"]["evidence_records"], 20)
        self.assertIn("ransomware", dashboard["coverage"]["threats"])
        self.assertIn("AU", dashboard["localization"]["covered_countries"])
        self.assertTrue(dashboard["install_release"]["pyproject"])
        self.assertEqual(len(dashboard["data_pack"]["fingerprint"]), 64)
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)
        self.assertEqual(dashboard["readiness_gate"]["status"], "needs_source_review")
        self.assertGreaterEqual(len(dashboard["next_actions"]), 3)
        self.assertEqual(dashboard["next_actions"][0]["priority"], "P0")
        self.assertEqual(
            dashboard["feed_governance"]["problem_feeds"][0]["id"],
            "asd_annual_cyber_threat_report_2024_2025",
        )

    def test_readiness_dashboard_formats_for_console(self):
        dashboard = build_readiness_dashboard(ROOT)
        output = format_readiness_dashboard(dashboard)

        self.assertIn("Global readiness dashboard", output)
        self.assertIn("Gate: needs_source_review", output)
        self.assertIn("Next actions", output)
        self.assertIn("Data pack:", output)
        self.assertIn("Installable package: True", output)


if __name__ == "__main__":
    unittest.main()
