import json
import tempfile
import unittest
from pathlib import Path

from engine.data_packs import (
    PACK_PATHS,
    build_data_pack_manifest,
    build_data_pack_release,
    write_data_pack_manifest,
    write_data_pack_release,
)


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

    def test_pack_covers_the_values_that_are_actually_simulated(self):
        """A release fingerprint must cover the numbers it publishes.

        `scenarios` was missing from PACK_PATHS until 2026-07-30. A scenario file holds
        the frequency and impact the Monte Carlo runs, so a shard could drift away from
        its calibration -- publishing a loss range its evidence did not produce -- inside
        a released pack whose fingerprint never moved. Citations pinned to that release
        (ADR-0004) would have claimed integrity over the evidence but not the numbers.
        """
        self.assertIn("scenarios", PACK_PATHS)
        self.assertIn("calibrations", PACK_PATHS)
        self.assertIn("evidence", PACK_PATHS)

        manifest = build_data_pack_manifest(ROOT)
        covered = {entry["path"].split("/", 1)[0] for entry in manifest["files"]}
        self.assertIn("scenarios", covered)

    def test_data_pack_manifest_can_be_written(self):
        manifest = build_data_pack_manifest(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            output = write_data_pack_manifest(manifest, Path(tmp) / "pack.json")
            payload = json.loads(output.read_text())

        self.assertEqual(payload["fingerprint"], manifest["fingerprint"])

    def test_data_pack_release_can_be_written_with_version(self):
        release = build_data_pack_release(
            ROOT,
            version="2026.06.15-test",
            notes="Test release",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = write_data_pack_release(release, Path(tmp))
            payload = json.loads(output.read_text())

        self.assertEqual(output.name, "2026.06.15-test.json")
        self.assertEqual(payload["release_type"], "riskshard_data_pack_release")
        self.assertEqual(payload["release_version"], "2026.06.15-test")
        self.assertEqual(payload["fingerprint"], release["manifest"]["fingerprint"])
        self.assertEqual(payload["notes"], "Test release")
        self.assertEqual(len(payload["source_manifest_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
