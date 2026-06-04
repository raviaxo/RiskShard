import unittest
from pathlib import Path

from engine.calibration_assistant import (
    format_module_calibration_proposal,
    propose_module_calibration,
)
from engine.country_priorities import (
    find_country_priority,
    format_country_priorities,
    load_country_priorities,
)
from engine.evidence_packs import (
    build_evidence_pack_registry,
    format_evidence_pack_detail,
    format_evidence_pack_registry,
)
from engine.risk_modules import (
    find_risk_module,
    format_module_detail,
    format_module_list,
    load_risk_modules,
    module_for_scenario,
    search_risk_modules,
)


ROOT = Path(__file__).resolve().parents[1]


class RiskModuleTests(unittest.TestCase):
    def test_module_catalog_loads_governed_starters(self):
        modules = load_risk_modules(ROOT)
        module_ids = {module["id"] for module in modules}
        output = format_module_list(search_risk_modules("finance", ROOT))

        self.assertEqual(len(modules), 5)
        self.assertIn("au_finance_ransomware_midmarket", module_ids)
        self.assertIn("au_finance_data_breach_midmarket", module_ids)
        self.assertIn("au_finance_bec_midmarket", module_ids)
        self.assertIn("gb_finance_data_breach_midmarket", module_ids)
        self.assertIn("us_finance_bec_midmarket", module_ids)
        self.assertIn("Risk modules", output)
        self.assertIn("governed_starter", output)

    def test_module_detail_and_scenario_lookup(self):
        module = find_risk_module("business_email_compromise", ROOT)
        output = format_module_detail(module)
        by_scenario = module_for_scenario(ROOT / "scenarios" / "business_email_compromise.yaml", ROOT)

        self.assertEqual(module["id"], "au_finance_bec_midmarket")
        self.assertEqual(by_scenario["id"], "au_finance_bec_midmarket")
        self.assertIn("Risk module: au_finance_bec_midmarket", output)
        self.assertIn("Calibration:", output)

    def test_evidence_pack_registry_summarizes_sources_and_assumptions(self):
        registry = build_evidence_pack_registry(ROOT)
        output = format_evidence_pack_registry(registry)
        ransomware = build_evidence_pack_registry(ROOT, "au_finance_ransomware_midmarket")["packs"][0]
        detail = format_evidence_pack_detail(ransomware)

        self.assertEqual(registry["pack_count"], 5)
        self.assertIn("Evidence packs", output)
        self.assertEqual(ransomware["freshness_status"], "current")
        self.assertEqual(ransomware["pack_confidence"], "low")
        self.assertIn("frequency.max: assumption_only", detail)
        self.assertIn("source_gathered", detail)

    def test_module_calibration_proposal_exposes_current_and_best_selectors(self):
        proposal = propose_module_calibration("au_finance_ransomware_midmarket", ROOT)
        output = format_module_calibration_proposal(proposal)
        by_parameter = {item["parameter"]: item for item in proposal["selectors"]}

        self.assertFalse(proposal["ready_without_assumptions"])
        self.assertEqual(by_parameter["frequency.likely"]["status"], "selected_source_backed")
        self.assertEqual(by_parameter["frequency.max"]["status"], "selected_assumption")
        self.assertIn("Module calibration proposal: au_finance_ransomware_midmarket", output)
        self.assertIn("draft: frequency.likely", output)

    def test_country_priorities_list_twenty_five_contribution_targets(self):
        priorities = load_country_priorities()
        output = format_country_priorities(priorities)
        us = find_country_priority("US")
        gb = find_country_priority("GB")

        self.assertEqual(len(priorities["items"]), 25)
        self.assertEqual(us["recommended_first_module"], "us_finance_bec_midmarket")
        self.assertEqual(us["status"], "module_seeded")
        self.assertEqual(gb["recommended_first_module"], "gb_finance_data_breach_midmarket")
        self.assertEqual(gb["status"], "module_seeded")
        self.assertIn("Country expansion priorities", output)
        self.assertIn("US", output)


if __name__ == "__main__":
    unittest.main()
