"""Edition staleness: does a parameter cite a superseded edition?

Two of these tests exist because the first version of this module was wrong in a way
that looked right. It resolved a card's source by matching `source_name` against the
registry title, and the Australia record says "Sophos The State of Ransomware in
Australia 2025" where the registry says "The State of Ransomware in Australia 2025
(whitepaper)". The check returned two rows, none of them the one already confirmed by
hand, and an under-reporting check reads exactly like a clean bill of health.
"""
import unittest

from engine.editions import (edition_groups, superseded_anchors, title_stem,
                             _source_by_evidence_id)
from engine.project_paths import find_project_root
from engine.source_audit import load_registry

ROOT = find_project_root()


class TitleStemTests(unittest.TestCase):
    def test_the_edition_year_is_what_the_stem_removes(self):
        self.assertEqual(title_stem("The State of Ransomware in Australia 2025"),
                         title_stem("The State of Ransomware in Australia 2026"))

    def test_how_we_stored_a_copy_is_not_what_it_measures(self):
        """'(whitepaper, archived snapshot)' and '(global report)' are our packaging.

        Without this the 2023 and 2024 globals did not pair with the 2026 global, and
        the check silently under-reported.
        """
        self.assertEqual(title_stem("The State of Ransomware 2023 (whitepaper, archived snapshot)"),
                         title_stem("The State of Ransomware 2026 (global report)"))

    def test_a_sector_cut_is_not_an_edition_of_a_country_cut(self):
        """The bias runs toward missing a pair rather than inventing one: a false pair
        would put a manufacturing figure forward as the successor to an Australian one."""
        self.assertNotEqual(title_stem("The State of Ransomware in Australia 2025"),
                            title_stem("The State of Ransomware in Manufacturing 2025"))


class SupersededAnchorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = superseded_anchors(ROOT)

    def test_the_australia_impact_anchor_is_found(self):
        """Confirmed by hand before the module existed, so it is the regression case.

        `au_finance_ransomware_midmarket.impact.likely` is the Sophos Australia 2025
        mean recovery cost of USD 650,000. The 2026 country cut is registered, read and
        verified, and states that figure rose to USD 1.66M. docs/CROSS_SOURCE.md
        publishes the 2026 number on the same site as the shard built on the 2025 one.
        """
        hits = [r for r in self.rows
                if r["module_id"] == "au_finance_ransomware_midmarket"
                and r["parameter"] == "impact.likely"]
        self.assertEqual(len(hits), 1, "the Australia impact anchor stopped being detected")
        self.assertEqual(hits[0]["cites"], "sophos_state_ransomware_australia_2025")
        self.assertEqual(hits[0]["superseded_by"], "sophos_state_ransomware_au_2026")

    def test_source_identity_comes_from_the_declared_link_not_a_title_match(self):
        """The bug that hid the case above. Evidence records declare `source_id`; the
        provenance card carries only a display string, and matching on it fails
        silently for any record whose prose name differs from the registry title."""
        index = _source_by_evidence_id(ROOT)
        self.assertEqual(index.get("sophos_au_2025_ransomware_recovery_cost_usd"),
                         "sophos_state_ransomware_australia_2025")

    def test_every_row_carries_the_reason_the_older_edition_was_chosen(self):
        """An older edition is frequently deliberate — a stress bound wants a
        genuinely different reading, not a fresher one. A flag without the rationale
        beside it presents a considered choice as a defect, and gets ignored."""
        for row in self.rows:
            self.assertIn("rationale", row, row["parameter"])
        explained = [r for r in self.rows if (r.get("rationale") or "").strip()]
        self.assertEqual(len(explained), len(self.rows),
                         "an anchor cites a superseded edition with no recorded reason")

    def test_rows_name_both_editions_and_their_dates(self):
        for row in self.rows:
            self.assertTrue(row["cites"] and row["superseded_by"], row["parameter"])
            self.assertLess(row["cites_date"], row["successor_date"], row["parameter"])

    def test_groups_are_ordered_oldest_first(self):
        for members in edition_groups(load_registry(ROOT)).values():
            dates = [str(m.get("publication_date") or "") for m in members]
            self.assertEqual(dates, sorted(dates))


if __name__ == "__main__":
    unittest.main()
