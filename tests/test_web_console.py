import unittest
from pathlib import Path

from engine.web_console import INDEX_HTML, WebConsoleApp


ROOT = Path(__file__).resolve().parents[1]


class WebConsoleTests(unittest.TestCase):
    def test_web_console_runs_commands_and_preserves_state(self):
        app = WebConsoleApp(root=ROOT)

        workflow = app.run_command("workflow")
        self.assertIn("First-run workflow", workflow["output"])
        self.assertEqual(workflow["prompt"], "riskshard> ")

        selected = app.run_command("use au_finance_ransomware_midmarket")
        self.assertIn("Using Risk Shard au_finance_ransomware_midmarket", selected["output"])
        self.assertIn("Location: [Start] > [Scenario]", selected["output"])
        self.assertEqual(selected["prompt"], "riskshard(au_finance_ransomware_midmarket)> ")
        self.assertEqual(selected["active_module_id"], "au_finance_ransomware_midmarket")

        where = app.run_command("where")
        self.assertIn("Consume model", where["output"])
        self.assertIn("Enhance model", where["output"])

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
        self.assertIn("Risk Shards", modules["output"])

        riskshards = app.run_command("riskshards")
        self.assertIn("Risk Shards", riskshards["output"])

        registry = app.run_command("registry")
        self.assertIn("RiskShard registry", registry["output"])
        self.assertIn("Shard packs", registry["output"])

        countries = app.run_command("countries")
        self.assertIn("Country expansion priorities", countries["output"])
        self.assertIn("us_finance_bec_midmarket", countries["output"])
        self.assertIn("gb_finance_data_breach_midmarket", countries["output"])

        gb = app.run_command("countries GB")
        self.assertIn("Country priority: GB", gb["output"])
        self.assertIn("Next gap", gb["output"])

        packs = app.run_command("packs")
        self.assertIn("Evidence pack: au_finance_ransomware_midmarket", packs["output"])

        proposal = app.run_command("propose")
        self.assertIn("Module calibration proposal: au_finance_ransomware_midmarket", proposal["output"])

        run = app.run_command("run")
        self.assertIn("Run complete.", run["output"])
        self.assertIn("Run receipt", run["output"])
        self.assertIn("Risk Shard    : au_finance_ransomware_midmarket", run["output"])
        self.assertIn("Simulation    : trials=10000, dist=pert, seed=42", run["output"])
        self.assertIn("LEC: results/lec_Console.png", run["output"])

        gb_proposal = app.run_command("propose gb_finance_data_breach_midmarket")
        self.assertIn("country=GB", gb_proposal["output"])
        self.assertIn("Ready without assumptions: True", gb_proposal["output"])

        actions = app.run_command("next")
        self.assertIn("Next best actions", actions["output"])
        self.assertIn("Fill missing direct evidence", actions["output"])

        dashboard = app.dashboard()
        self.assertIn("coverage", dashboard)
        self.assertIn("data_pack", dashboard)
        self.assertIn("next_actions", dashboard)
        self.assertEqual(dashboard["active_module_id"], "au_finance_ransomware_midmarket")
        self.assertIn("coverage_matrix", dashboard["evidence_packs"])
        self.assertEqual(dashboard["risk_modules"]["module_count"], 11)
        self.assertEqual(dashboard["evidence_packs"]["pack_count"], 11)
        self.assertEqual(dashboard["readiness_gate"]["status"], "ready_for_local_calibrated_run")
        self.assertGreaterEqual(len(dashboard["top_risks"]), 5)

    def test_browser_console_uses_practitioner_risk_shard_language(self):
        self.assertIn("What is a Risk Shard?", INDEX_HTML)
        self.assertIn("Risk Shard Catalog", INDEX_HTML)
        self.assertIn("Where am I?", INDEX_HTML)
        self.assertIn("Consume model path", INDEX_HTML)
        self.assertIn("Enhance model path", INDEX_HTML)
        self.assertIn("Shard registry", INDEX_HTML)
        self.assertIn("Start over", INDEX_HTML)
        self.assertIn("commandFolder(command)", INDEX_HTML)
        self.assertIn("[Start] $ system", INDEX_HTML)
        self.assertIn("United Kingdom contribution detail", INDEX_HTML)
        self.assertIn("GB is the taxonomy code for the UK.", INDEX_HTML)
        self.assertIn("height: 100vh;", INDEX_HTML)
        self.assertIn("overflow-y: auto;", INDEX_HTML)
        self.assertIn('id="console-scroll"', INDEX_HTML)
        self.assertIn("flex: 0 0 auto;", INDEX_HTML)
        self.assertIn("Every button runs a real console command.", INDEX_HTML)
        self.assertIn("Risk Shards for this context", INDEX_HTML)
        self.assertIn("Trust boundary", INDEX_HTML)
        self.assertIn('commandButton(`use ${row.module_id}`, "Use")', INDEX_HTML)
        self.assertIn('commandButton(`packs ${row.module_id}`, "Evidence")', INDEX_HTML)

    def test_browser_console_handles_api_failures_without_stale_running_state(self):
        self.assertIn("async function requestJson", INDEX_HTML)
        self.assertIn("Command failed: ${error.message}", INDEX_HTML)
        self.assertIn("Browser console could not reach the local RiskShard server", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
