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
        self.assertIn("GB", dashboard["localization"]["covered_countries"])
        self.assertTrue(dashboard["install_release"]["pyproject"])
        self.assertEqual(len(dashboard["data_pack"]["fingerprint"]), 64)
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)
        self.assertEqual(dashboard["scenarios"]["stage_counts"]["governed_starter"], 5)
        self.assertEqual(dashboard["scenarios"]["stage_counts"]["demo_fixture"], 5)
        self.assertEqual(dashboard["risk_modules"]["module_count"], 5)
        self.assertEqual(dashboard["evidence_packs"]["pack_count"], 5)
        self.assertEqual(len(dashboard["evidence_packs"]["coverage_matrix"]), 5)
        gb = next(
            row for row in dashboard["evidence_packs"]["coverage_matrix"]
            if row["module_id"] == "gb_finance_data_breach_midmarket"
        )
        self.assertEqual(gb["source_backed_direct"], 5)
        self.assertEqual(gb["assumption_only_direct"], 1)
        self.assertIn("impact.max", gb["next_gap"])
        self.assertEqual(
            dashboard["readiness_gate"]["status"],
            "ready_for_local_calibrated_run",
        )
        self.assertEqual(dashboard["feed_governance"]["problem_feeds"], [])
        self.assertGreaterEqual(len(dashboard["next_actions"]), 3)
        self.assertNotEqual(dashboard["next_actions"][0]["priority"], "P0")

    def test_readiness_dashboard_formats_for_console(self):
        dashboard = build_readiness_dashboard(ROOT)
        output = format_readiness_dashboard(dashboard)

        self.assertIn("Global readiness dashboard", output)
        self.assertIn("Gate: ready_for_local_calibrated_run", output)
        self.assertIn("Next actions", output)
        self.assertIn("Data pack:", output)
        self.assertIn("Scenarios: demo_fixture=5, governed_starter=5", output)
        self.assertIn("Risk modules: 5", output)
        self.assertIn("Evidence packs: 5", output)
        self.assertIn("Module coverage matrix", output)
        self.assertIn("gb_finance_data_breach_midmarket: 5/6 source-backed", output)
        self.assertIn("Installable package: True", output)


if __name__ == "__main__":
    unittest.main()
