import unittest
from pathlib import Path

from engine.doctor import build_doctor_report, format_doctor_report, parse_project_scripts


ROOT = Path(__file__).resolve().parents[1]


class DoctorTests(unittest.TestCase):
    def test_doctor_summarizes_local_readiness(self):
        report = build_doctor_report(ROOT)
        output = format_doctor_report(report)
        checks = {item["name"]: item for item in report["checks"]}

        self.assertEqual(report["status"], "pass")
        # Calibration drift is reported loudly but does not gate yet: four shards still
        # simulate values their calibrations no longer produce (found 2026-07-30).
        # Correcting one moves a published number, so it is an owner decision.
        self.assertIn("DRIFT", checks["calibration drift"]["detail"])
        self.assertIn("RiskShard doctor", output)
        self.assertEqual(checks["sources"]["status"], "pass")
        self.assertIn("governed_starter=15", checks["scenarios"]["detail"])
        self.assertIn("demo_fixture=5", checks["scenarios"]["detail"])
        self.assertEqual(checks["package entry points"]["status"], "pass")
        self.assertIn("run with --run-tests", checks["tests"]["detail"])
        # the strength ledger is caught up to the current data pack in-repo
        self.assertEqual(checks["strength ledger"]["status"], "pass")
        self.assertIn("caught up", checks["strength ledger"]["detail"])

    def test_parse_project_scripts_reads_entry_points(self):
        text = """
[project.scripts]
riskshard = "scripts.fair_calc:main"
riskshard-doctor = "scripts.riskshard_doctor:main"

[tool.setuptools]
packages = ["engine"]
"""

        self.assertEqual(
            parse_project_scripts(text),
            ["riskshard", "riskshard-doctor"],
        )


if __name__ == "__main__":
    unittest.main()
