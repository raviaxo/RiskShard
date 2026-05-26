import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliSmokeTests(unittest.TestCase):
    def test_cli_runs_against_sample_scenarios(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/fair_calc.py",
                "scenarios",
                "--trials",
                "25",
                "--seed",
                "1",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("=== PORTFOLIO ===", result.stdout)
        self.assertIn("Ransomware Attack", result.stdout)
        self.assertIn("LEC saved:", result.stdout)

    def test_cli_runs_contextual_analysis(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "contextual_report.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/fair_calc.py",
                    "scenarios/au_finance_ransomware_midmarket.yaml",
                    "--org-profile",
                    "org_profiles/au_finance_midmarket.yaml",
                    "--control-profile",
                    "control_profiles/ransomware_basic_controls.yaml",
                    "--provenance",
                    "provenance/au_finance_ransomware_midmarket.yaml",
                    "--trials",
                    "25",
                    "--seed",
                    "1",
                    "--report-output",
                    str(report_path),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
            self.assertTrue(report_path.exists())

        self.assertIn("=== CONTEXTUAL ANALYSIS ===", result.stdout)
        self.assertIn("Confidence: low", result.stdout)


if __name__ == "__main__":
    unittest.main()
