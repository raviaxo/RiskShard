import unittest
from pathlib import Path

from engine.profiles import load_yaml_file


ROOT = Path(__file__).resolve().parents[1]


class ThreatLibraryTests(unittest.TestCase):
    def test_starter_threat_library_uses_vetted_threat_ids(self):
        taxonomy = load_yaml_file(ROOT / "taxonomies" / "threats.yaml")
        library = load_yaml_file(ROOT / "threat_library" / "starter_pack.yaml")

        taxonomy_ids = {item["id"] for item in taxonomy["items"]}
        library_ids = {item["id"] for item in library["threats"]}

        self.assertTrue(library_ids.issubset(taxonomy_ids))
        self.assertEqual(
            {
                "ransomware",
                "data_breach",
                "business_email_compromise",
                "third_party_outage",
                "insider_misuse",
            },
            library_ids,
        )

    def test_each_starter_threat_has_required_evidence_and_sources(self):
        library = load_yaml_file(ROOT / "threat_library" / "starter_pack.yaml")

        for threat in library["threats"]:
            with self.subTest(threat=threat["id"]):
                self.assertGreaterEqual(len(threat["required_evidence"]), 3)
                self.assertGreaterEqual(len(threat["starter_sources"]), 1)


if __name__ == "__main__":
    unittest.main()
