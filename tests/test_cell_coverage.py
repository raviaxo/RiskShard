"""ADR-0018's preconditions, recomputed from live data instead of trusted.

The ADR retired the reader-target selector because the corpus could not answer the
questions the control invited. It then named what would have to change before it
came back. Those conditions are worth exactly as much as their last measurement, so
they are measured here on every run.

If one of these tests fails because a precondition became TRUE, nothing is broken —
it means the corpus grew into the feature and ADR-0018 is owed a revisit.
"""
import unittest

from engine.cell_coverage import cell_coverage, matched_count, offered_values, _parameters
from engine.project_paths import find_project_root
from scripts.build_explorer import build_data

ROOT = find_project_root()


class CellCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shards = build_data(ROOT)["shards"]
        cls.coverage = cell_coverage(cls.shards)

    def test_the_grid_is_measured_under_the_engines_own_facet_keys(self):
        """The first measurement of this read size under the wrong key.

        An ad-hoc script used `sizes` where the payload says `company_size_bands`,
        so the size facet was silently never tested and the grid came out 215
        instead of 539. Pinning the key here is what stops that recurring: a facet
        that is never tested looks like a facet that always matches.
        """
        values = offered_values(self.shards)
        self.assertGreater(len(values["size"]), 1,
                           "size resolved to a single value: the facet key is probably wrong")
        for facet in ("country", "industry", "size", "threat"):
            self.assertTrue(values[facet], f"{facet} offered no values")

    def test_a_majority_of_nameable_cells_still_cannot_be_answered(self):
        """ADR-0018 precondition 2. False today, and the reason the control is gone."""
        c = self.coverage
        self.assertFalse(
            c["majority_answered"],
            f"ADR-0018 precondition 2 is now met ({c['answered']} of {c['combinations']} "
            f"answered): the target selector is owed a revisit.",
        )
        self.assertGreater(c["empty_share"], 0.5)

    def test_trap_pairs_still_exist(self):
        """ADR-0018 precondition 1. A pair that each answer alone and nothing together.

        This is the shape a reader walks into one dropdown at a time, and it is what
        was reported from the live page: Australia answers, manufacturing answers,
        Australia + manufacturing answers nothing.
        """
        c = self.coverage
        self.assertFalse(
            c["no_traps"],
            "ADR-0018 precondition 1 is now met: no dead ends and no trap pairs remain.",
        )
        params = _parameters(self.shards)
        self.assertGreater(matched_count(params, {"country": "AU"}), 0)
        self.assertGreater(matched_count(params, {"industry": "manufacturing"}), 0)
        self.assertEqual(matched_count(params, {"country": "AU", "industry": "manufacturing"}), 0)

    def test_the_adr_quotes_the_numbers_this_module_computes(self):
        """A measurement in prose drifts from the data unless something checks it."""
        adr = (ROOT / "docs" / "adr" /
               "0018-the-target-selector-failed-measurement.md").read_text(encoding="utf-8")
        c = self.coverage
        for figure in (str(c["combinations"]), str(c["empty"]), str(len(c["trap_pairs"]))):
            self.assertIn(figure, adr, f"ADR-0018 no longer states {figure}")


if __name__ == "__main__":
    unittest.main()
