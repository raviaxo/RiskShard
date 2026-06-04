import unittest
from pathlib import Path

from engine.extractions import load_extractions, validate_extractions


ROOT = Path(__file__).resolve().parents[1]


class ExtractionTests(unittest.TestCase):
    def test_reviewed_extractions_load_and_map_to_evidence(self):
        records = load_extractions(ROOT / "extractions")

        self.assertGreaterEqual(len(records), 8)
        self.assertIn(
            "sophos_fin_services_hit_rate_2024",
            {record["id"] for record in records},
        )
        self.assertIn(
            "fbi_ic3_2025_bec_average_loss_per_complaint_usd",
            {record["id"] for record in records},
        )

    def test_reviewed_extractions_have_no_mapping_errors(self):
        issues = validate_extractions(
            ROOT / "extractions",
            ROOT / "evidence",
            ROOT / "sources" / "manifest.json",
        )

        self.assertFalse(
            any(issue["severity"] == "error" for issue in issues),
            issues,
        )


if __name__ == "__main__":
    unittest.main()
