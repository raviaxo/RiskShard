import unittest
from datetime import date
from pathlib import Path

from engine.governance import build_data_feed_inventory, format_data_feed_inventory


ROOT = Path(__file__).resolve().parents[1]


class GovernanceTests(unittest.TestCase):
    def test_data_feed_inventory_separates_source_gather_and_evidence_ingestion(self):
        inventory = build_data_feed_inventory(
            registry_path=ROOT / "sources" / "registry.yaml",
            manifest_path=ROOT / "sources" / "manifest.json",
            evidence_path=ROOT / "evidence",
            today=date(2026, 6, 4),
        )
        by_id = {feed["id"]: feed for feed in inventory["feeds"]}
        oaic = by_id["oaic_ndb_jul_dec_2024"]
        abs_feed = by_id["abs_counts_australian_businesses_2025"]
        fbi = by_id["fbi_ic3_2025_report"]
        uk_dsit = by_id["uk_dsit_cyber_breaches_2026"]
        ibm_uk = by_id["ibm_cost_data_breach_uk_2025"]
        fca_equifax = by_id["fca_equifax_cyber_breach_fine_2023"]
        accc = by_id["accc_targeting_scams_2025"]
        business_qld = by_id["business_qld_cyber_secure_guidance_2025"]
        privacy_act = by_id["privacy_act_1988_latest"]

        self.assertEqual(oaic["source_status"], "fetched")
        self.assertIsNotNone(oaic["source_gathered_at"])
        self.assertEqual(oaic["riskshard_evidence_ingested_at"], "2026-06-03")
        self.assertEqual(oaic["trust_tier"], "high")
        self.assertEqual(oaic["evidence_confidence"], "medium")
        self.assertEqual(oaic["renewal_status"], "current")
        self.assertEqual(abs_feed["source_status"], "fetched")
        self.assertEqual(abs_feed["trust_tier"], "high")
        self.assertEqual(abs_feed["evidence_record_count"], 4)
        self.assertEqual(fbi["trust_tier"], "high")
        self.assertEqual(fbi["evidence_record_count"], 7)  # SG BEC frequency floor moved to SPF/SingStat
        self.assertEqual(uk_dsit["trust_tier"], "high")
        self.assertEqual(uk_dsit["evidence_record_count"], 9)
        self.assertEqual(ibm_uk["trust_tier"], "medium")
        self.assertEqual(ibm_uk["evidence_record_count"], 2)
        self.assertEqual(fca_equifax["source_status"], "fetched")
        self.assertEqual(fca_equifax["trust_tier"], "high")
        self.assertEqual(fca_equifax["evidence_record_count"], 1)
        self.assertEqual(fca_equifax["evidence_confidence"], "medium")
        self.assertEqual(accc["trust_tier"], "high")
        self.assertEqual(accc["evidence_record_count"], 6)  # AU BEC impact.max moved to the AFP documented event
        self.assertEqual(business_qld["source_status"], "fetched")
        self.assertEqual(business_qld["trust_tier"], "medium")
        self.assertEqual(business_qld["evidence_record_count"], 2)
        self.assertEqual(privacy_act["source_status"], "fetched")
        self.assertEqual(privacy_act["trust_tier"], "high")
        self.assertEqual(privacy_act["evidence_record_count"], 1)
        self.assertEqual(privacy_act["riskshard_evidence_ingested_at"], "2026-07-14")

    def test_governance_skips_inactive_sources(self):
        inventory = build_data_feed_inventory(today=date(2026, 6, 3))
        by_id = {feed["id"]: feed for feed in inventory["feeds"]}
        output = format_data_feed_inventory(inventory)

        self.assertNotIn("asd_annual_cyber_threat_report_2024_2025", by_id)
        self.assertNotIn("gather_error", inventory["status_counts"])
        self.assertIn("source gathered", output.replace("_", " "))


if __name__ == "__main__":
    unittest.main()


class AdrIndexTests(unittest.TestCase):
    """Every ADR must appear in the index that claims to list them all.

    `docs/adr/README.md` is how a reader — and every future session — discovers what
    has been decided. An ADR missing from it is a decision that exists on disk and
    nowhere anyone looks, which is most of the way to not having recorded it.

    ADR-0015 was written and left out of the index for a day before this test
    existed, which is the whole argument for it.
    """

    def test_every_adr_file_is_listed(self):
        adr_dir = ROOT / "docs" / "adr"
        index = (adr_dir / "README.md").read_text(encoding="utf-8")
        missing = [p.name for p in sorted(adr_dir.glob("0*.md"))
                   if p.name not in index]
        self.assertEqual(missing, [], f"not linked from docs/adr/README.md: {missing}")

    def test_the_index_lists_no_adr_that_does_not_exist(self):
        import re

        adr_dir = ROOT / "docs" / "adr"
        index = (adr_dir / "README.md").read_text(encoding="utf-8")
        linked = set(re.findall(r"\((0\d{3}-[a-z0-9-]+\.md)\)", index))
        self.assertTrue(linked, "expected the index to link ADRs")
        for name in sorted(linked):
            self.assertTrue((adr_dir / name).exists(), f"index links a missing ADR: {name}")
