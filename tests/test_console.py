import io
import tempfile
import unittest
from pathlib import Path

from engine.console import RiskShardConsole


ROOT = Path(__file__).resolve().parents[1]


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.console = RiskShardConsole(root=ROOT, stdout=self.output)

    def command(self, text):
        self.output.seek(0)
        self.output.truncate(0)
        self.console.onecmd(text)
        return self.output.getvalue()

    def test_search_and_use_selects_recommended_calibration_inputs(self):
        workflow_output = self.command("workflow")
        self.assertIn("First-run workflow", workflow_output)
        self.assertIn("modules", workflow_output)
        self.assertIn("countries", workflow_output)
        self.assertIn("use gb_finance_data_breach_midmarket", workflow_output)

        search_output = self.command("search ransomware")
        self.assertIn("au_finance_ransomware_midmarket", search_output)
        self.assertIn("governed starter", search_output)
        self.assertIn("demo fixture", search_output)
        self.assertIn("Ransomware", search_output)

        use_output = self.command("use au_finance_ransomware_midmarket")
        self.assertIn("Using Risk Shard au_finance_ransomware_midmarket", use_output)
        self.assertIn("show options", use_output)

        options_output = self.command("show options")
        self.assertIn("Risk Shard    : au_finance_ransomware_midmarket", options_output)
        self.assertIn("scenarios/au_finance_ransomware_midmarket.yaml", options_output)
        self.assertIn("org_profiles/au_finance_midmarket.yaml", options_output)
        self.assertIn("calibrations/au_finance_ransomware.yaml", options_output)
        self.assertIn("threat       : ransomware", options_output)

        bec_output = self.command("use business_email_compromise")
        self.assertIn("Using Risk Shard au_finance_bec_midmarket", bec_output)
        bec_options = self.command("show options")
        self.assertIn("calibrations/au_finance_business_email_compromise.yaml", bec_options)
        self.assertIn("threat       : business_email_compromise", bec_options)

        info_output = self.command("info business_email_compromise")
        self.assertIn("Stage     : governed starter", info_output)
        self.assertIn("Benchmark :", info_output)

    def test_calibrate_writes_artifacts_and_exposes_selected_evidence(self):
        self.command("use au_finance_ransomware_midmarket")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            report_path = tmp_path / "calibration.json"
            markdown_path = tmp_path / "calibration.md"
            scenario_path = tmp_path / "calibrated.yaml"

            self.command(f"set report {report_path}")
            self.command(f"set markdown {markdown_path}")
            self.command(f"set scenario {scenario_path}")
            calibration_output = self.command("calibrate")

            self.assertTrue(report_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertTrue(scenario_path.exists())

        self.assertIn("Calibration complete.", calibration_output)
        self.assertIn("Warnings :", calibration_output)
        self.assertEqual(self.console.active_run_path, scenario_path)

        evidence_output = self.command("show evidence")
        self.assertIn("frequency.min:", evidence_output)
        self.assertIn("score=", evidence_output)
        self.assertIn("best=", evidence_output)

    def test_validate_reports_clean_evidence_quality(self):
        validate_output = self.command("validate")
        self.assertIn("Evidence quality gates passed with no issues.", validate_output)

    def test_top_risks_and_gaps_are_available_from_console(self):
        risks_output = self.command("toprisks")
        self.assertIn("Using default org profile:", risks_output)
        self.assertIn("Ransomware", risks_output)
        self.assertIn("Data Breach", risks_output)

        self.command("use au_finance_ransomware_midmarket")
        gaps_output = self.command("show gaps")
        self.assertIn("Gap analysis: ransomware", gaps_output)
        self.assertIn("Scenario parameters", gaps_output)
        self.assertIn("Next steps", gaps_output)

    def test_feed_governance_is_available_from_console(self):
        feeds_output = self.command("feeds")
        self.assertIn("Data feed governance", feeds_output)
        self.assertIn("source_gathered:", feeds_output)
        self.assertIn("evidence_ingested:", feeds_output)

        detail_output = self.command("feeds oaic_ndb_jul_dec_2024")
        self.assertIn("oaic_ndb_jul_dec_2024", detail_output)
        self.assertIn("sha256:", detail_output)

    def test_readiness_pack_and_proposal_are_available_from_console(self):
        readiness_output = self.command("readiness")
        self.assertIn("Global readiness dashboard", readiness_output)
        self.assertIn("Data pack:", readiness_output)

        pack_output = self.command("pack")
        self.assertIn("Data pack manifest", pack_output)
        self.assertIn("Fingerprint:", pack_output)

        proposal_output = self.command("propose data_breach")
        self.assertIn("Module calibration proposal: au_finance_data_breach_midmarket", proposal_output)
        self.assertIn("Selectors", proposal_output)

        modules_output = self.command("modules")
        self.assertIn("Risk Shards", modules_output)
        self.assertIn("au_finance_ransomware_midmarket", modules_output)
        self.assertIn("us_finance_bec_midmarket", modules_output)
        self.assertIn("gb_finance_data_breach_midmarket", modules_output)

        countries_output = self.command("countries")
        self.assertIn("Country expansion priorities", countries_output)
        self.assertIn("us_finance_bec_midmarket", countries_output)
        self.assertIn("gb_finance_data_breach_midmarket", countries_output)

        country_detail = self.command("countries GB")
        self.assertIn("Country priority: GB", country_detail)
        self.assertIn("Next gap", country_detail)

        module_info = self.command("modules info au_finance_ransomware_midmarket")
        self.assertIn("Risk Shard: au_finance_ransomware_midmarket", module_info)

        packs_output = self.command("packs au_finance_ransomware_midmarket")
        self.assertIn("Evidence pack: au_finance_ransomware_midmarket", packs_output)
        self.assertIn("source_gathered", packs_output)

        module_proposal = self.command("propose au_finance_ransomware_midmarket")
        self.assertIn("Module calibration proposal: au_finance_ransomware_midmarket", module_proposal)
        self.assertIn("selected_assumption", module_proposal)

        gb_proposal = self.command("propose gb_finance_data_breach_midmarket")
        self.assertIn("Module calibration proposal: gb_finance_data_breach_midmarket", gb_proposal)
        self.assertIn("country=GB", gb_proposal)
        self.assertIn("Ready without assumptions: True", gb_proposal)

        preflight_output = self.command("preflight")
        self.assertIn("Contributor preflight", preflight_output)
        self.assertIn("data pack fingerprint", preflight_output)

        doctor_output = self.command("doctor")
        self.assertIn("RiskShard doctor", doctor_output)
        self.assertIn("package entry points", doctor_output)
        self.assertIn("scenarios", doctor_output)

    def test_run_simulates_selected_scenario(self):
        self.command("use ransomware")
        self.command("set trials 5")
        run_output = self.command("run")

        self.assertIn("Run complete.", run_output)
        self.assertIn("P95", run_output)
        self.assertIn("LEC:", run_output)
        self.assertIsNotNone(self.console.last_run)
        self.assertTrue(self.console.last_paths["lec"].exists())


if __name__ == "__main__":
    unittest.main()
