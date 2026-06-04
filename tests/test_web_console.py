import unittest
from pathlib import Path

from engine.web_console import WebConsoleApp


ROOT = Path(__file__).resolve().parents[1]


class WebConsoleTests(unittest.TestCase):
    def test_web_console_runs_commands_and_preserves_state(self):
        app = WebConsoleApp(root=ROOT)

        workflow = app.run_command("workflow")
        self.assertIn("First-run workflow", workflow["output"])
        self.assertEqual(workflow["prompt"], "riskshard> ")

        selected = app.run_command("use au_finance_ransomware_midmarket")
        self.assertIn("Using module au_finance_ransomware_midmarket", selected["output"])
        self.assertEqual(selected["prompt"], "riskshard(au_finance_ransomware_midmarket)> ")

        options = app.run_command("show options")
        self.assertIn("org_profiles/au_finance_midmarket.yaml", options["output"])
        self.assertEqual(options["prompt"], "riskshard(au_finance_ransomware_midmarket)> ")

        risks = app.run_command("toprisks")
        self.assertIn("Top risks", risks["output"])
        self.assertIn("Data Breach", risks["output"])

        feeds = app.run_command("feeds")
        self.assertIn("Data feed governance", feeds["output"])
        self.assertIn("source_gathered:", feeds["output"])

        modules = app.run_command("modules")
        self.assertIn("Risk modules", modules["output"])

        packs = app.run_command("packs")
        self.assertIn("Evidence pack: au_finance_ransomware_midmarket", packs["output"])

        proposal = app.run_command("propose")
        self.assertIn("Module calibration proposal: au_finance_ransomware_midmarket", proposal["output"])

        actions = app.run_command("next")
        self.assertIn("Next best actions", actions["output"])
        self.assertIn("Replace assumptions", actions["output"])

        dashboard = app.dashboard()
        self.assertIn("coverage", dashboard)
        self.assertIn("data_pack", dashboard)
        self.assertIn("next_actions", dashboard)
        self.assertEqual(dashboard["risk_modules"]["module_count"], 3)
        self.assertEqual(dashboard["evidence_packs"]["pack_count"], 3)
        self.assertEqual(dashboard["readiness_gate"]["status"], "ready_for_local_calibrated_run")
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)


if __name__ == "__main__":
    unittest.main()
