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
        self.assertIn("Using Australia Finance Ransomware Midmarket", selected["output"])
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

        actions = app.run_command("next")
        self.assertIn("Next best actions", actions["output"])
        self.assertIn("Restore governed source feed health", actions["output"])

        dashboard = app.dashboard()
        self.assertIn("coverage", dashboard)
        self.assertIn("data_pack", dashboard)
        self.assertIn("next_actions", dashboard)
        self.assertEqual(dashboard["readiness_gate"]["status"], "needs_source_review")
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)


if __name__ == "__main__":
    unittest.main()
