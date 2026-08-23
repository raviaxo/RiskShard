"""The failure condition for nearest-shard borrowing, stated before it was built.

ADR-0018's amendment requires a design that never returns nothing to state its own
failure condition in advance, because ADR-0014 shipped a control decided on what the
page could cheaply compute and never on what its answers would say. This is that
condition, and it fired: the feature is declined in ADR-0019 without a line of it
being written.
"""
import unittest

from engine.borrowing import SECTOR_WEIGHTED, borrowing_profile, empty_cells
from engine.project_paths import find_project_root
from scripts.build_explorer import build_data

ROOT = find_project_root()


class BorrowingCeilingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shards = build_data(ROOT)["shards"]
        cls.profile = borrowing_profile(cls.shards)

    def test_the_answers_a_reader_could_receive_are_capped_by_the_shard_count(self):
        """The structural argument, asserted rather than reasoned about.

        A borrowed answer is some shard's answer, so the number of distinct answers
        cannot exceed the number of shards however the donor is chosen. 456 cells
        collapse onto 11 figures.
        """
        self.assertLessEqual(self.profile["distinct_answers"], self.profile["shards"])
        self.assertGreater(self.profile["cells"], 40 * self.profile["distinct_answers"])

    def test_most_cells_have_no_single_nearest_shard(self):
        """The sharper number. Where several shards are equally near, which figure the
        reader receives falls to an ordering that carries no evidentiary meaning."""
        self.assertGreater(self.profile["tie_share"], 0.5)

    def test_weighting_the_facets_does_not_rescue_it(self):
        """Sector-weighting is the obvious fix and the intake scorer's own ranking.
        It cannot raise the ceiling, and here it makes the tie rate worse."""
        weighted = borrowing_profile(self.shards, SECTOR_WEIGHTED)
        self.assertEqual(weighted["distinct_answers"], self.profile["distinct_answers"])
        self.assertGreaterEqual(weighted["tie_share"], self.profile["tie_share"])

    def test_the_population_is_the_cells_the_corpus_cannot_answer(self):
        cells = empty_cells(self.shards)
        self.assertEqual(len(cells), self.profile["cells"])
        self.assertTrue(all(cell for cell in cells))

    def test_the_adr_quotes_the_figures_it_declines_on(self):
        """ADR-0019 argues from these numbers; if they move, the argument is owed a
        re-read rather than a silent survival."""
        adr = (ROOT / "docs" / "adr" / "0019-borrowing-cannot-answer-an-unpublished-cell.md"
               ).read_text(encoding="utf-8")
        profile = self.profile
        for figure in (str(profile["cells"]), str(profile["distinct_answers"]),
                       f"{profile['tie_share']:.0%}"):
            self.assertIn(figure, adr, f"ADR-0019 no longer states {figure}")


if __name__ == "__main__":
    unittest.main()
