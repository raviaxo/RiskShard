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
        accc = by_id["accc_targeting_scams_2025"]
        business_qld = by_id["business_qld_cyber_secure_guidance_2025"]

        self.assertEqual(oaic["source_status"], "fetched")
        self.assertIsNotNone(oaic["source_gathered_at"])
        self.assertEqual(oaic["riskshard_evidence_ingested_at"], "2026-06-03")
        self.assertEqual(oaic["trust_tier"], "high")
        self.assertEqual(oaic["evidence_confidence"], "medium")
        self.assertEqual(oaic["renewal_status"], "current")
        self.assertEqual(abs_feed["source_status"], "fetched")
        self.assertEqual(abs_feed["trust_tier"], "high")
        self.assertEqual(abs_feed["evidence_record_count"], 2)
        self.assertEqual(fbi["trust_tier"], "high")
        self.assertEqual(fbi["evidence_record_count"], 3)
        self.assertEqual(accc["trust_tier"], "high")
        self.assertEqual(accc["evidence_record_count"], 4)
        self.assertEqual(business_qld["source_status"], "fetched")
        self.assertEqual(business_qld["trust_tier"], "medium")
        self.assertEqual(business_qld["evidence_record_count"], 1)

    def test_governance_skips_inactive_sources(self):
        inventory = build_data_feed_inventory(today=date(2026, 6, 3))
        by_id = {feed["id"]: feed for feed in inventory["feeds"]}
        output = format_data_feed_inventory(inventory)

        self.assertNotIn("asd_annual_cyber_threat_report_2024_2025", by_id)
        self.assertNotIn("gather_error", inventory["status_counts"])
        self.assertIn("source gathered", output.replace("_", " "))


if __name__ == "__main__":
    unittest.main()
