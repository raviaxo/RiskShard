import json
import tempfile
import unittest
from pathlib import Path

from engine.data_packs import build_data_pack_manifest, write_data_pack_manifest


ROOT = Path(__file__).resolve().parents[1]


class DataPackTests(unittest.TestCase):
    def test_data_pack_manifest_fingerprints_governed_inputs(self):
        manifest = build_data_pack_manifest(ROOT)

        self.assertGreater(manifest["file_count"], 10)
        self.assertEqual(len(manifest["fingerprint"]), 64)
        self.assertIn("sources/manifest.json", manifest["paths"])
        self.assertIn("risk_modules", manifest["paths"])
        self.assertIn(
            "evidence/au_finance_ransomware.yaml",
            {item["path"] for item in manifest["files"]},
        )
        self.assertIn(
            "risk_modules/au_finance_ransomware_midmarket.yaml",
            {item["path"] for item in manifest["files"]},
        )

    def test_data_pack_manifest_can_be_written(self):
        manifest = build_data_pack_manifest(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = write_data_pack_manifest(manifest, Path(tmp) / "pack.json")
            payload = json.loads(output.read_text())

        self.assertEqual(payload["fingerprint"], manifest["fingerprint"])


if __name__ == "__main__":
    unittest.main()
