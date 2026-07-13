import json
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
        self.assertIn("=== PORTFOLIO (unconverted mixed/unspecified currencies) ===", result.stdout)
        self.assertIn("WARNING: Portfolio statistics are an unconverted arithmetic sum", result.stdout)
        self.assertIn("Ransomware Attack", result.stdout)
        self.assertIn("STAGE: demo fixture", result.stdout)
        self.assertIn("STAGE: governed starter", result.stdout)
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

        self.assertIn("=== PORTFOLIO (AUD) ===", simulation.stdout)
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

    def test_doctor_cli_reports_ready_status(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [
                sys.executable,
                "scripts/riskshard_doctor.py",
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
        self.assertIn("RiskShard doctor", result.stdout)
        self.assertIn("Status: pass", result.stdout)

    def test_data_pack_cli_writes_named_release(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/data_pack_manifest.py",
                    "--release",
                    "2026.06.15-test",
                    "--release-dir",
                    tmp,
                    "--notes",
                    "CLI smoke release",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
            release_path = Path(tmp) / "2026.06.15-test.json"

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(release_path.exists())

        self.assertIn("Data-pack release saved:", result.stdout)
        self.assertIn("Data pack release", result.stdout)

    def test_modules_cli_reports_catalog_packs_and_proposals(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        list_result = subprocess.run(
            [sys.executable, "scripts/riskshard_modules.py", "list"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(list_result.returncode, 0, msg=list_result.stderr)
        self.assertIn("Risk Shards", list_result.stdout)
        self.assertIn("au_finance_ransomware_midmarket", list_result.stdout)

        pack_result = subprocess.run(
            [
                sys.executable,
                "scripts/riskshard_modules.py",
                "packs",
                "au_finance_ransomware_midmarket",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(pack_result.returncode, 0, msg=pack_result.stderr)
        self.assertIn("Evidence pack: au_finance_ransomware_midmarket", pack_result.stdout)
        self.assertIn("source_gathered", pack_result.stdout)

        proposal_result = subprocess.run(
            [
                sys.executable,
                "scripts/riskshard_modules.py",
                "propose",
                "au_finance_ransomware_midmarket",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proposal_result.returncode, 0, msg=proposal_result.stderr)
        self.assertIn(
            "Module calibration proposal: au_finance_ransomware_midmarket",
            proposal_result.stdout,
        )
        self.assertIn("selected_assumption", proposal_result.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "ransomware_pack.json"
            export_result = subprocess.run(
                [
                    sys.executable,
                    "scripts/riskshard_modules.py",
                    "packs",
                    "au_finance_ransomware_midmarket",
                    "--export",
                    str(export_path),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(export_result.returncode, 0, msg=export_result.stderr)
            self.assertTrue(export_path.exists())
            exported = json.loads(export_path.read_text())

        self.assertEqual(exported["artifact_type"], "riskshard_module_evidence_pack")
        self.assertIn("Evidence pack artifact saved:", export_result.stdout)
        self.assertIn("Fingerprint:", export_result.stdout)

        countries_result = subprocess.run(
            [
                sys.executable,
                "scripts/riskshard_modules.py",
                "countries",
                "--limit",
                "5",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(countries_result.returncode, 0, msg=countries_result.stderr)
        self.assertIn("Country expansion priorities", countries_result.stdout)
        self.assertIn("us_finance_bec_midmarket", countries_result.stdout)
        self.assertIn("gb_finance_data_breach_midmarket", countries_result.stdout)

    def test_top_risks_cli_reports_ranked_threats(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [sys.executable, "scripts/riskshard_toprisks.py", "--limit", "3"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Top risks", result.stdout)
        self.assertIn("Data Breach", result.stdout)

        json_result = subprocess.run(
            [sys.executable, "scripts/riskshard_toprisks.py", "--limit", "2", "--json"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(json_result.returncode, 0, msg=json_result.stderr)
        payload = json.loads(json_result.stdout)
        self.assertEqual(payload["risk_count"], 2)
        self.assertEqual(payload["risks"][0]["id"], "data_breach")
        self.assertIn("missing_parameters", payload["risks"][0])

    def test_package_smoke_cli_verifies_entry_points(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [sys.executable, "scripts/package_smoke.py"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("RiskShard package smoke", result.stdout)
        self.assertIn("riskshard-toprisks", result.stdout)
        self.assertIn("riskshard-package-smoke", result.stdout)

    def test_benchmark_program_cli_reports_thirty_target_gate(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        result = subprocess.run(
            [sys.executable, "scripts/benchmark_program.py", "--target", "gb_finance_data_breach_midmarket"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Benchmark-Grade 30 Shard Program", result.stdout)
        self.assertIn("Targets: 30", result.stdout)
        self.assertIn("benchmark-ready: 1", result.stdout)
        self.assertIn("confidence>=medium=6/6", result.stdout)

        cohort_result = subprocess.run(
            [sys.executable, "scripts/benchmark_program.py", "--cohort", "seeded"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(cohort_result.returncode, 0, msg=cohort_result.stderr)
        self.assertIn("Benchmark Cohort 1: seeded modules", cohort_result.stdout)
        self.assertIn("Upgrade queue", cohort_result.stdout)
        self.assertIn("au_finance_ransomware_midmarket", cohort_result.stdout)

        sprint_result = subprocess.run(
            [sys.executable, "scripts/benchmark_program.py", "--sprint", "seeded"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(sprint_result.returncode, 0, msg=sprint_result.stderr)
        self.assertIn("Seeded Evidence Upgrade Sprint A", sprint_result.stdout)
        self.assertIn("Acceptance criteria", sprint_result.stdout)
        self.assertIn(
            "python scripts/riskshard_modules.py propose au_finance_ransomware_midmarket",
            sprint_result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
