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
                for source_id in record.get("source_ids", []):
                    self.assertIn(source_id, manifest_by_id)
                if "source_ids" in record:
                    self.assertIn(record["source_id"], record["source_ids"])
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
            records["sophos_au_2025_ransomware_recovery_cost_usd"]["currency"],
            "USD",
        )

    def test_starter_packs_cover_data_breach_and_bec_honestly(self):
        records = load_evidence_records(ROOT / "evidence")
        by_id = {record["id"]: record for record in records}

        self.assertEqual(
            by_id["oaic_au_finance_data_breach_notifications_2024_h2"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["verizon_dbir_2026_vulnerability_exploitation_breach_entry_share"]["value"],
            0.31,
        )
        self.assertEqual(
            by_id["verizon_dbir_2026_third_party_breach_involvement_share"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["riskshard_data_breach_frequency_likely_2026"]["evidence_type"],
            "estimated",
        )
        self.assertEqual(
            by_id["uk_dsit_2026_medium_business_breach_prevalence_au_bridge"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["uk_dsit_2026_medium_business_breach_prevalence_au_bridge"]["value"],
            0.65,
        )
        self.assertEqual(
            by_id["uk_dsit_2026_medium_business_breach_prevalence_au_bridge"]["applicability"]["countries"],
            ["global"],
        )
        self.assertEqual(
            by_id["uk_dsit_2026_large_business_breach_prevalence_au_stress_bridge"]["value"],
            0.69,
        )
        self.assertEqual(
            by_id["abs_au_financial_insurance_active_businesses_2025"]["value"],
            133743,
        )
        self.assertEqual(
            by_id["oaic_abs_au_finance_ndb_notification_rate_floor_2025"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["oaic_abs_au_finance_ndb_notification_rate_floor_2025"]["confidence"],
            "medium",
        )
        self.assertEqual(
            by_id["oaic_abs_au_finance_ndb_notification_rate_floor_2025"]["source_ids"],
            ["oaic_ndb_jul_dec_2024", "abs_counts_australian_businesses_2025"],
        )
        self.assertEqual(
            by_id["securitybrief_ibm_2026_au_finserv_breach_average_cost_aud"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["securitybrief_ibm_2026_au_finserv_breach_average_cost_aud"]["value"],
            6310000,
        )
        self.assertEqual(
            by_id["cyentia_iris_2025_extreme_security_incident_loss_usd"]["currency"],
            "USD",
        )
        self.assertEqual(
            by_id["fbi_ic3_2025_bec_average_loss_per_complaint_usd"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["fbi_ic3_2025_bec_average_loss_per_complaint_usd"]["value"],
            123005.43,
        )
        self.assertEqual(
            by_id["fbi_ic3_2025_bec_average_loss_per_complaint_usd"]["currency"],
            "USD",
        )
        self.assertEqual(
            by_id["accc_2025_small_business_false_billing_losses_aud"]["value"],
            2000000,
        )
        self.assertEqual(
            by_id["riskshard_bec_impact_likely_2026"]["applicability"]["threats"],
            ["business_email_compromise"],
        )
        self.assertIn(
            "Not source-backed",
            by_id["riskshard_bec_impact_likely_2026"]["limitations"],
        )
        self.assertEqual(
            by_id["uk_dsit_2026_medium_business_breach_prevalence"]["value"],
            0.65,
        )
        self.assertEqual(
            by_id["ibm_uk_2025_financial_services_breach_average_cost_gbp"]["currency"],
            "GBP",
        )
        self.assertEqual(
            by_id["fca_equifax_2023_cyber_breach_fine_gbp"]["evidence_type"],
            "source_backed",
        )
        self.assertEqual(
            by_id["fca_equifax_2023_cyber_breach_fine_gbp"]["value"],
            11164400,
        )
        self.assertEqual(
            by_id["fca_equifax_2023_cyber_breach_fine_gbp"]["confidence"],
            "medium",
        )
        self.assertIn(
            "not total event loss",
            by_id["fca_equifax_2023_cyber_breach_fine_gbp"]["limitations"],
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
            "sophos_2024_au_ransomware_attack_rate_likely",
        )
        self.assertEqual(
            summary["best_by_parameter"]["frequency.likely"]["applicability"]["country"]["match"],
            "exact",
        )
        # The frequency floor is still the global Cyentia bridge - the fallback
        # explanation is exercised there.
        self.assertEqual(
            summary["best_by_parameter"]["frequency.min"]["id"],
            "cyentia_global_ransomware_probability_2025",
        )
        self.assertEqual(
            summary["best_by_parameter"]["frequency.min"]["applicability"]["country"]["match"],
            "fallback",
        )
        self.assertEqual(
            summary["best_by_parameter"]["impact.min"]["applicability"]["country"]["match"],
            "exact",
        )


if __name__ == "__main__":
    unittest.main()
