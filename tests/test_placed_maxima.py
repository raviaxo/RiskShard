"""The five `none_known` maxima carry their placement, and its figures are not typed.

ADR-0024 found that this repo's own source audit had recorded an exceedance
denominator that ADR-0008, `engine/exceedance.py` and finding 3 all published as
missing, and held that refutation for 88 days. The ADR placed every published
maximum in the distribution but deliberately scoped out the records themselves,
so for three more days the five `none_known` maxima carried `limitations` text
written before the distribution existed — a caveat getting quieter by default,
which AGENTS.md names as a defect in its own right.

The caveats were written on 2026-11-14 and they carry four figures each into
reader-facing text. A figure typed into prose has no owner and nothing watching
it, so this module is the owner: every number in those five records is asserted
against `engine.tail_bracket` on every run, and the whole point of the exercise
is lost if one of them is allowed to drift.

Three of the five sit *below* their tier's 95th percentile. A reader treating
one of those as an outer bound is wrong in the direction that costs money, which
is why the placement belongs on the record and not only in a finding.
"""
import unittest

from engine.exceedance import BASES
from engine.project_paths import find_project_root
from engine.tail_bracket import SOURCE_NAME, build_portfolio_brackets, load_evidence_records

ROOT = find_project_root()


def _placed():
    brackets = build_portfolio_brackets(ROOT)
    return [m for m in brackets["modules"] if m["exceedance_basis"] == "none_known"]


def _records():
    return {r["id"]: r for r in load_evidence_records()}


class PlacedMaximaTests(unittest.TestCase):
    def setUp(self):
        self.placed = _placed()
        self.records = _records()

    def test_there_are_still_five_of_them(self):
        """Not a magic number — it is the count ADR-0024 measured and this file covers.

        If it moves, a maximum was re-anchored or a new one landed, and either way
        the caveats below need re-reading rather than silently covering fewer records.
        """
        self.assertEqual(len(self.placed), 5,
                         "the none_known maxima changed — re-read the placements")

    def test_every_figure_in_every_caveat_comes_from_the_engine(self):
        for module in self.placed:
            with self.subTest(module=module["module_id"]):
                limitations = self.records[module["evidence_id"]]["limitations"]
                self.assertIn(SOURCE_NAME, limitations)
                self.assertIn(f"USD {round(module['p95']):,}", limitations)
                self.assertIn(f"USD {round(module['usd']):,}", limitations)
                self.assertIn(f"{module['ratio_to_p95']:.2f}x", limitations)
                self.assertIn(module["meaning"], limitations)

    def test_the_placement_did_not_re_anchor_anything(self):
        """ADR-0024 decline 2. A placement reports; it never moves the anchor."""
        for module in self.placed:
            with self.subTest(module=module["module_id"]):
                record = self.records[module["evidence_id"]]
                self.assertEqual(record["exceedance_basis"], "none_known")
                self.assertEqual(record["value"], module["value"])
                self.assertIn("exceedance_basis stays none_known",
                              record["limitations"])

    def test_no_fifth_exceedance_basis_was_minted(self):
        """ADR-0024 decline 1. The bracket is a caveat, never a rung on the ladder."""
        self.assertEqual(
            set(BASES),
            {"modeled_quantile", "observed_rank", "population_ceiling", "none_known"},
        )
        for record in self.records.values():
            if "exceedance_basis" in record:
                self.assertIn(record["exceedance_basis"], BASES)

    def test_the_caveat_says_it_is_all_cause_against_a_threat_specific_anchor(self):
        """ADR-0007's construct warning is the reason this is a caveat and not a swap.

        IRIS Table 1 is all-cause cyber loss; every one of these five anchors is
        threat-specific. Dropping that sentence would make the placement read as a
        like-for-like comparison, which is the exact confusion ADR-0007 exists to
        prevent — so it is asserted rather than trusted to survive an edit.
        """
        for module in self.placed:
            with self.subTest(module=module["module_id"]):
                self.assertIn("all-cause distribution placed against a threat-specific",
                              self.records[module["evidence_id"]]["limitations"])


if __name__ == "__main__":
    unittest.main()
