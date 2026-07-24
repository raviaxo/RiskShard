import tempfile
import unittest
from pathlib import Path

from engine.scaffold import (
    org_profile_stem,
    scaffold_id,
    scaffold_paths,
    scaffold_shard,
)


class ScaffoldNamingTests(unittest.TestCase):
    def test_id_matches_house_convention(self):
        # financial_services -> finance, business_email_compromise -> bec, mid_market -> midmarket
        self.assertEqual(
            scaffold_id("GB", "financial_services", "mid_market", "business_email_compromise"),
            "gb_finance_bec_midmarket",
        )
        self.assertEqual(
            scaffold_id("BR", "retail", "mid_market", "ransomware"),
            "br_retail_ransomware_midmarket",
        )

    def test_org_profile_stem_matches_existing(self):
        self.assertEqual(org_profile_stem("GB", "financial_services", "mid_market"), "gb_finance_midmarket")


class ScaffoldGenerateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_six_wired_files(self):
        result = scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware")
        self.assertEqual(result["shard_id"], "br_retail_ransomware_midmarket")
        for key in ("module", "scenario", "org_profile", "calibration", "evidence", "extractions"):
            self.assertTrue((self.root / result["paths"][key]).exists(), f"{key} not written")

    def test_module_points_at_the_files_it_wrote(self):
        scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware")
        module = (self.root / "risk_modules" / "br_retail_ransomware_midmarket.yaml").read_text()
        self.assertIn("scenarios/br_retail_ransomware_midmarket.yaml", module)
        self.assertIn("org_profiles/br_retail_midmarket.yaml", module)
        self.assertIn("status: scaffold", module)

    def test_scenario_stage_is_schema_valid_and_placeholders_marked(self):
        scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware")
        scenario = (self.root / "scenarios" / "br_retail_ransomware_midmarket.yaml").read_text()
        self.assertIn("scenario_stage: governed_starter", scenario)  # 'scaffold' is not schema-valid
        evidence = (self.root / "evidence" / "br_retail_ransomware_midmarket.yaml").read_text()
        self.assertIn("evidence_type: estimated", evidence)
        self.assertIn("SCAFFOLD", evidence)                          # honestly not source-backed

    def test_dry_run_writes_nothing(self):
        result = scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware", dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse((self.root / result["paths"]["module"]).exists())

    def test_refuses_to_clobber_without_overwrite(self):
        scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware")
        with self.assertRaises(ValueError):
            scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware")
        # overwrite succeeds
        scaffold_shard(self.root, "BR", "retail", "mid_market", "ransomware", overwrite=True)


if __name__ == "__main__":
    unittest.main()
