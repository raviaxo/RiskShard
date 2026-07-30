import unittest
from pathlib import Path

from engine.beta_readiness import build_beta_readiness_report, format_beta_readiness_report


ROOT = Path(__file__).resolve().parents[1]


class BetaReadinessTests(unittest.TestCase):
    def test_beta_readiness_gate_prioritizes_product_depth_before_ops(self):
        report = build_beta_readiness_report(ROOT)
        output = format_beta_readiness_report(report)
        checks = {item["id"]: item for item in report["checks"]}

        self.assertEqual(report["gate"]["status"], "beta_ready")
        self.assertEqual(report["gate"]["passed"], 11)
        self.assertEqual(report["gate"]["total"], 11)
        self.assertEqual(checks["BETA-DATA-01"]["status"], "pass")
        self.assertEqual(checks["BETA-DATA-02"]["status"], "pass")
        self.assertEqual(checks["BETA-DATA-02"]["actual"], 11)
        self.assertEqual(checks["BETA-DATA-02"]["target"], 10)
        self.assertEqual(checks["BETA-DATA-03"]["status"], "pass")
        self.assertEqual(checks["BETA-DATA-03"]["actual"], 6)
        self.assertEqual(checks["BETA-DATA-03"]["target"], 3)
        self.assertEqual(checks["BETA-ENG-03"]["status"], "pass")
        self.assertEqual(checks["BETA-GOV-01"]["status"], "pass")
        self.assertEqual(checks["BETA-GOV-02"]["status"], "pass")
        self.assertNotIn("Seed 4 more governed starter modules", output)
        self.assertNotIn("Promote 1 more module", output)
        self.assertIn("RiskShard is ready for beta review", output)
        self.assertNotIn("Record clean-install verification", output)
        self.assertIn("Deferred until beta", output)
        self.assertIn("public contributor campaign", output)


if __name__ == "__main__":
    unittest.main()
