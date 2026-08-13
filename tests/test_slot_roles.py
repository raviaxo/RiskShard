"""The anchor-slot declaration: does an anchor's measured quantity fit its slot's role?

A beta-PERT's second parameter is a mode. Nothing here supplies one. These tests pin
the measured counts, the structural claim behind them, and the two reader-facing
surfaces the declaration has to reach — the same discipline ADR-0007's tests apply,
for the same reason: a caveat only counts where it is published.
"""
import glob
import json
import unittest
from pathlib import Path

import yaml

from engine.provenance import build_module_provenance, build_portfolio_provenance
from engine.slot_roles import (
    CENTRAL_TENDENCY_BASES,
    MODAL_BASES,
    build_portfolio_slot_roles,
    slot_declarations,
)

ROOT = Path(__file__).resolve().parents[1]

#: The eight, from the mechanical inventory in docs/internal/anchor_slot_inventory.md.
#: Published as seven until the 2026-08-12 recount; pinned so it cannot silently drift back.
MODE_SLOT_CENTRAL_TENDENCY = {
    "au_finance_bec_midmarket",
    "au_finance_data_breach_midmarket",
    "ca_finance_data_breach_midmarket",
    "fr_finance_data_breach_midmarket",
    "gb_finance_data_breach_midmarket",
    "sg_finance_bec_midmarket",
    "us_finance_bec_midmarket",
    "us_finance_data_breach_midmarket",
}


class VocabularyTests(unittest.TestCase):
    """The structural claim: the schema cannot express a mode."""

    def test_no_declared_basis_denotes_a_mode(self):
        schema = json.loads(
            (ROOT / "schemas" / "evidence_record_schema.json").read_text(encoding="utf-8")
        )
        vocabulary = set(
            schema["properties"]["records"]["items"]["properties"]["measurement_basis"]["enum"]
        )
        self.assertEqual(
            MODAL_BASES & vocabulary,
            set(),
            "a modal measurement_basis now exists — the mode-slot declaration must be "
            "revisited rather than left standing",
        )

    def test_central_tendency_bases_are_real_vocabulary_entries(self):
        schema = json.loads(
            (ROOT / "schemas" / "evidence_record_schema.json").read_text(encoding="utf-8")
        )
        vocabulary = set(
            schema["properties"]["records"]["items"]["properties"]["measurement_basis"]["enum"]
        )
        self.assertTrue(CENTRAL_TENDENCY_BASES <= vocabulary)


class PortfolioCountTests(unittest.TestCase):
    """The published counts, re-derived rather than trusted."""

    def setUp(self):
        self.portfolio = build_portfolio_slot_roles(ROOT)
        self.totals = self.portfolio["totals"]

    def test_no_impact_likely_anchor_is_a_mode(self):
        self.assertEqual(
            self.totals["mode_slot_declarations"], self.totals["shards"],
            "every shard's impact.likely must carry a mode-slot declaration",
        )

    def test_eight_shards_put_a_central_tendency_in_the_mode_slot(self):
        self.assertEqual(self.totals["shards_mode_slot_central_tendency"], 8)
        found = {
            m["module_id"]
            for m in self.portfolio["modules"]
            for d in m["declarations"]
            if d["kind"] == "mode_slot" and d["central_tendency"]
        }
        self.assertEqual(found, MODE_SLOT_CENTRAL_TENDENCY)

    def test_seven_shards_use_a_central_tendency_as_the_floor(self):
        self.assertEqual(self.totals["shards_floor_slot"], 7)

    def test_six_shards_do_both(self):
        both = sum(
            1
            for m in self.portfolio["modules"]
            if any(d["kind"] == "floor_slot" for d in m["declarations"])
            and any(d["kind"] == "mode_slot" and d["central_tendency"] for d in m["declarations"])
        )
        self.assertEqual(both, 6)

    def test_a_cost_component_at_likely_is_declared_but_not_called_central_tendency(self):
        provenance = build_module_provenance("de_industrial_ransomware_midmarket", ROOT)
        mode = [d for d in slot_declarations(provenance) if d["kind"] == "mode_slot"]
        self.assertEqual(len(mode), 1)
        self.assertFalse(mode[0]["central_tendency"])
        self.assertIn("not a calibrated mode", mode[0]["headline"])


class CalibrationRecordTests(unittest.TestCase):
    """ADR-0009: the reason a number occupies a slot lives in the calibration rationale."""

    def test_every_central_tendency_anchor_declares_its_slot_in_prose(self):
        declared = 0
        for path in sorted(glob.glob(str(ROOT / "calibrations" / "*.yaml"))):
            payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
            impact = (payload.get("parameters") or {}).get("impact") or {}
            for slot, spec in impact.items():
                if isinstance(spec, dict) and "Slot declaration" in (spec.get("rationale") or ""):
                    declared += 1
        self.assertEqual(
            declared, 15,
            "8 mode-slot plus 7 floor-slot anchors must carry a written slot declaration",
        )


class PublishedSurfaceTests(unittest.TestCase):
    """The declaration has to reach a reader, not just the CLI."""

    def test_evidence_report_carries_the_headline_and_per_anchor_callouts(self):
        markdown = __import__(
            "engine.provenance", fromlist=["format_portfolio_markdown"]
        ).format_portfolio_markdown(build_portfolio_provenance(ROOT))
        self.assertIn("**Anchor slot roles:**", markdown)
        self.assertIn("not a calibrated mode", markdown)
        self.assertIn("not an observed minimum", markdown)

    def test_explorer_payload_carries_a_slot_declaration_per_shard(self):
        from scripts.build_explorer import build_data

        data = build_data(ROOT)
        for shard in data["shards"]:
            kinds = [d["kind"] for d in shard.get("slots", [])]
            self.assertIn(
                "mode_slot", kinds, f"{shard['id']} must declare what occupies its mode slot"
            )
            for declaration in shard["slots"]:
                self.assertTrue(declaration["headline"])
                self.assertTrue(declaration["detail"])


if __name__ == "__main__":
    unittest.main()
