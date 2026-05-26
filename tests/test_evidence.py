import json
import unittest
from pathlib import Path

from engine.evidence import load_evidence_records, match_evidence, summarize_match
from engine.profiles import load_org_profile
from engine.taxonomy import normalize_context


ROOT = Path(__file__).resolve().parents[1]


class TaxonomyTests(unittest.TestCase):
    def test_normalize_context_maps_org_profile_and_threat_to_ids(self):
        profile = load_org_profile(ROOT / "org_profiles" / "au_finance_midmarket.yaml")

        context = normalize_context(profile, "ransomware")

        self.assertEqual(context, {
            "industry": "financial_services",
            "country": "AU",
            "company_size": "mid_market",
            "threat": "ransomware",
        })


class EvidenceMatchingTests(unittest.TestCase):
    def test_load_evidence_records_validates_schema(self):
        records = load_evidence_records(ROOT / "evidence")

        self.assertGreaterEqual(len(records), 10)
        self.assertIn("frequency.likely", {record["parameter"] for record in records})

    def test_source_backed_records_map_to_source_manifest(self):
        manifest = json.loads((ROOT / "sources" / "manifest.json").read_text())
        manifest_by_id = {source["id"]: source for source in manifest["sources"]}
        records = load_evidence_records(ROOT / "evidence")

        for record in records:
            if record["evidence_type"] != "source_backed":
                continue

            with self.subTest(record=record["id"]):
                self.assertIn("source_id", record)
                self.assertIn(record["source_id"], manifest_by_id)
                source = manifest_by_id[record["source_id"]]
                self.assertEqual(record["publication_date"], source["publication_date"])
                self.assertIn(
                    record["source_url_or_citation"],
                    {source["url"], source["final_url"]},
                )
                self.assertIn("citation_detail", record)

                if source["status"] != "fetched":
                    self.assertIn("latest source gather did not retrieve", record["limitations"])

    def test_reviewed_pack_contains_australia_finance_ransomware_context(self):
        records = {
            record["id"]: record
            for record in load_evidence_records(ROOT / "evidence" / "au_finance_ransomware.yaml")
        }

        self.assertEqual(
            records["oaic_au_ransomware_ndb_notifications_2024_h2"]["source_id"],
            "oaic_ndb_jul_dec_2024",
        )
        self.assertEqual(
            records["cyentia_fin_services_ransomware_incident_share_2025"]["value"],
            0.15,
        )
        self.assertEqual(
            records["sophos_fin_services_ransomware_recovery_cost_2024"]["currency"],
            "USD",
        )

    def test_match_evidence_prefers_applicable_records_and_explains_fallbacks(self):
        profile = load_org_profile(ROOT / "org_profiles" / "au_finance_midmarket.yaml")
        records = load_evidence_records(ROOT / "evidence")

        result = match_evidence(records, profile, "ransomware")
        summary = summarize_match(result)

        self.assertGreaterEqual(result["match_count"], 6)
        self.assertEqual(summary["target_context"]["country"], "AU")
        self.assertEqual(
            summary["best_by_parameter"]["frequency.likely"]["id"],
            "sophos_fin_services_ransomware_frequency_2024",
        )
        self.assertEqual(
            summary["best_by_parameter"]["frequency.likely"]["applicability"]["country"]["match"],
            "fallback",
        )
        self.assertEqual(
            summary["best_by_parameter"]["impact.min"]["applicability"]["country"]["match"],
            "exact",
        )


if __name__ == "__main__":
    unittest.main()
