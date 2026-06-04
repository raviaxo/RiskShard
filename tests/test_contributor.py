import unittest
from pathlib import Path

from engine.contributor import build_contributor_preflight, format_contributor_preflight


ROOT = Path(__file__).resolve().parents[1]


class ContributorTests(unittest.TestCase):
    def test_contributor_preflight_summarizes_pack_readiness(self):
        preflight = build_contributor_preflight(ROOT)
        output = format_contributor_preflight(preflight)

        self.assertEqual(preflight["status"], "pass")
        self.assertIn("source registry", {item["name"] for item in preflight["checks"]})
        self.assertIn("data pack fingerprint", {item["name"] for item in preflight["checks"]})
        self.assertIn("Contributor preflight", output)
        self.assertIn("evidence quality: pass", output)


if __name__ == "__main__":
    unittest.main()
