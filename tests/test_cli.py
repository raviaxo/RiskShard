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

    def test_calibrated_scenario_can_be_simulated(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "calibration.json"
            scenario_path = Path(tmp) / "calibrated.yaml"
            calibration = subprocess.run(
                [
                    sys.executable,
                    "scripts/calibrate_scenario.py",
                    "scenarios/au_finance_ransomware_midmarket.yaml",
                    "--org-profile",
                    "org_profiles/au_finance_midmarket.yaml",
                    "--evidence",
                    "evidence",
                    "--calibration",
                    "calibrations/au_finance_ransomware.yaml",
                    "--threat",
                    "ransomware",
                    "--report-output",
                    str(report_path),
                    "--scenario-output",
                    str(scenario_path),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(
                calibration.returncode,
                0,
                msg=f"stdout:\n{calibration.stdout}\nstderr:\n{calibration.stderr}",
            )
            self.assertTrue(report_path.exists())
            self.assertTrue(scenario_path.exists())

            simulation = subprocess.run(
                [
                    sys.executable,
                    "scripts/fair_calc.py",
                    str(scenario_path),
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
                simulation.returncode,
                0,
                msg=f"stdout:\n{simulation.stdout}\nstderr:\n{simulation.stderr}",
            )

        self.assertIn("=== PORTFOLIO ===", simulation.stdout)
        self.assertIn("Australia Finance Ransomware Midmarket", simulation.stdout)

    def test_calibration_cli_writes_report_and_scenario(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "calibration.json"
            markdown_path = Path(tmp) / "calibration.md"
            scenario_path = Path(tmp) / "calibrated.yaml"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/calibrate_scenario.py",
                    "scenarios/au_finance_ransomware_midmarket.yaml",
                    "--org-profile",
                    "org_profiles/au_finance_midmarket.yaml",
                    "--evidence",
                    "evidence",
                    "--calibration",
                    "calibrations/au_finance_ransomware.yaml",
                    "--threat",
                    "ransomware",
                    "--report-output",
                    str(report_path),
                    "--markdown-output",
                    str(markdown_path),
                    "--scenario-output",
                    str(scenario_path),
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
            self.assertTrue(markdown_path.exists())
            self.assertTrue(scenario_path.exists())

        self.assertIn("=== CALIBRATED SCENARIO ===", result.stdout)
        self.assertIn("Markdown report saved:", result.stdout)
        self.assertIn("Warnings :", result.stdout)


if __name__ == "__main__":
    unittest.main()
