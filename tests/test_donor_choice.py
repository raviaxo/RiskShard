"""The reader-chosen-donor measurement, pinned so it cannot drift unnoticed.

`engine/donor_choice.py` states a failure condition and measures it. The condition and
both thresholds were committed before `measure()` was first run, which is the only thing
that makes the result a test rather than a description — see
`docs/internal/donor_choice_measurement.md`.

These assertions exist for two reasons.

**A threshold must not move after the fact.** The numbers in the module docstring are the
contract; if somebody edits 50% to 70% because a later corpus pushed a share over the
line, that is the move ADR-0017 stands as a standing warning against. The thresholds are
asserted here as literals so changing one has to be deliberate and visible in a diff.

**The measured shares are pinned loosely, not exactly.** The corpus changes — a shard
retiring or a facet value changing moves these numbers legitimately. So the bands are wide
enough to survive that and tight enough to fail if the verdict is about to flip, because a
verdict flipping is the event that deserves a human reading the result again rather than a
green suite.
"""

import unittest

from engine.borrowing import empty_cells
from engine.donor_choice import measure
from engine.project_paths import find_project_root
from scripts.build_explorer import build_data

ROOT = find_project_root()


class DonorChoiceMeasurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shards = build_data(ROOT)["shards"]
        cls.result = measure(cls.shards, empty_cells(cls.shards))

    def test_the_value_half_actually_ran(self):
        """The first draft reported `declines_on_values: false` on zero comparable cells.

        Every shard's figure failed to parse, so the spread test never ran, and a test
        that did not run was reporting as a test that passed — the same unmeasured-versus-
        zero defect ADR-0022 built a meter for. `measure()` now raises rather than return
        a verdict resting on it, and this asserts the half is populated.
        """
        self.assertGreater(
            self.result["comparable_cells"], 0,
            "the value-spread half produced no comparable cells, so the verdict rests on "
            "one measured condition and one that silently did not run",
        )
        self.assertIsNotNone(self.result["median_spread"])

    def test_tied_cells_still_agree_with_adr_0019(self):
        """271 of 456 is ADR-0019's own tie count. A divergence means one of the two
        modules changed what it counts, and they are supposed to be counting the same
        thing."""
        self.assertGreater(self.result["tied_cells"], 200)
        self.assertLess(self.result["tied_cells"], 320)

    def test_the_facet_half_clears_its_threshold(self):
        """28.0% measured against a 50% bar. Banded, because the corpus may move it."""
        self.assertLess(
            self.result["single_facet_set_share"], 0.50,
            "more than half of tied cells now offer the reader a single matched-facet "
            "set, which is the stated decline condition — re-read "
            "docs/internal/donor_choice_measurement.md before changing anything",
        )
        self.assertFalse(self.result["declines_on_facets"])

    def test_the_value_half_clears_its_threshold(self):
        """1.8% measured against a 50% bar."""
        self.assertLess(self.result["narrow_spread_share"], 0.50)
        self.assertFalse(self.result["declines_on_values"])

    def test_the_verdict_is_derived_not_asserted(self):
        """The verdict must follow from the two halves, never be set independently."""
        expected = (
            "decline"
            if (self.result["declines_on_facets"] or self.result["declines_on_values"])
            else "proceed"
        )
        self.assertEqual(self.result["verdict"], expected)

    def test_the_spread_between_tied_donors_is_large(self):
        """The finding the condition did not ask about, pinned because it is the reason
        the design owes a second measurement.

        A median of 8.83x means two equally-near donors hand over figures differing by
        nearly an order of magnitude. That clears the stated test — it is the opposite of
        'the choice does not move the answer' — and it is why choosing badly is expensive.
        If this ever falls near 1.0 the whole route changes character and the measurement
        document is wrong.
        """
        self.assertGreater(
            self.result["median_spread"], 2.0,
            "tied donors now give near-identical figures, which inverts the finding in "
            "docs/internal/donor_choice_measurement.md",
        )


class ThresholdsAreNotMovable(unittest.TestCase):
    def test_the_stated_thresholds_are_still_the_ones_in_the_docstring(self):
        """Both are 50%, fixed before the first run. Moving one must be deliberate."""
        from engine import donor_choice

        doc = donor_choice.__doc__
        self.assertIn("more than 50%", doc)
        self.assertIn("under\n  25%", doc.replace("\r\n", "\n"))

    def test_the_module_builds_no_feature(self):
        """ADR-0019 permits a measurement here, not an implementation."""
        from engine import donor_choice

        public = [n for n in dir(donor_choice) if not n.startswith("_")]
        self.assertIn("measure", public)
        for forbidden in ("borrow", "compose_answer", "answer_cell", "render"):
            self.assertNotIn(forbidden, public)


if __name__ == "__main__":
    unittest.main()
