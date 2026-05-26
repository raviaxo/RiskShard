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

        self.assertGreaterEqual(len(records), 6)
        self.assertIn("frequency.likely", {record["parameter"] for record in records})

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
