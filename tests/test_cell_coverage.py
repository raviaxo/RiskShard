"""ADR-0018's preconditions, recomputed from live data instead of trusted.

The ADR retired the reader-target selector because the corpus could not answer the
questions the control invited. It then named what would have to change before it
came back. Those conditions are worth exactly as much as their last measurement, so
they are measured here on every run.

If one of these tests fails because a precondition became TRUE, nothing is broken —
it means the corpus grew into the feature and ADR-0018 is owed a revisit.
"""
import unittest

from engine.cell_coverage import (answered_split, cell_coverage, matched_count, offered_values,
                                  shard_self_coverage, specificity_profile, _parameters)
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


class SpecificityTests(unittest.TestCase):
    """The empty share averages two different readers together. Split, it inverts."""

    @classmethod
    def setUpClass(cls):
        cls.shards = build_data(ROOT)["shards"]
        cls.profile = specificity_profile(cls.shards)

    def test_supplying_more_context_lowers_the_chance_of_an_answer(self):
        """The defect behind the composition work, and it is not thinness.

        A reader who names one facet is answered every time; one who names all four
        is answered twice in 192. Reading more sources raises every level without
        necessarily reversing the direction, so this needs its own measurement rather
        than being read off the headline empty share.

        If this test fails because `inverted` became False, the corpus grew out of
        the defect and the composition work is owed a revisit.
        """
        levels = self.profile["levels"]
        self.assertTrue(self.profile["inverted"],
                        f"context no longer degrades the answer: "
                        f"{ {n: round(l['answered_share'], 3) for n, l in sorted(levels.items())} }")
        self.assertEqual(levels[1]["answered_share"], 1.0)
        self.assertLess(levels[4]["answered_share"], 0.05)

    def test_a_fully_specified_cell_cannot_complete_a_shard_from_matched_anchors(self):
        """A shard needs six parameters. The best fully-specified cell matches three.

        This is why composition is the only mechanism by which reader-supplied
        context can exist at all: at this specificity there is no set of matched
        anchors to run, so every complete answer is necessarily assembled.
        """
        self.assertLess(self.profile["levels"][4]["best_matched"], 6)


class ShardSelfCoverageTests(unittest.TestCase):
    """The same rule turned on our own published numbers."""

    @classmethod
    def setUpClass(cls):
        cls.coverage = shard_self_coverage(build_data(ROOT)["shards"])

    def test_no_shard_is_measured_on_the_cell_it_is_named_after(self):
        """Every published shard is partly bridged, and the page has never said so.

        A parameter is measured on the shard's own cell only when its declared
        population names every facet that cell sets. `au_finance_ransomware_midmarket`
        matches none of its six; the best in the corpus matches half.

        A failure here is good news: some shard became complete on its own cell, and
        the disclosure this measurement supports needs rewriting rather than removing.
        """
        c = self.coverage
        self.assertFalse(
            c["any_shard_complete_on_own_cell"],
            "a shard is now fully measured on its own cell: the bridging disclosure is stale",
        )
        self.assertGreater(c["fully_bridged"], 0)
        self.assertTrue(all(row["facets_set"] == 4 for row in c["shards"]),
                        "a shard stopped declaring all four facets; the measurement is not comparable")

    def test_the_per_shard_split_sums_to_the_count_the_portfolio_publishes(self):
        """Two independent paths to the same number, tied together so they cannot drift.

        `engine/provenance.py` derives `params_cell_matched` from each record's
        declared population against its shard's cell; this module replays the rule
        from the explorer payload instead. They agree at 7 of 66. If they ever stop
        agreeing, one of them has quietly redefined what bridged means, and the
        published headline and the per-shard disclosure would then be telling a
        reader two different things about the same evidence.
        """
        from engine.provenance import build_portfolio_provenance
        totals = build_portfolio_provenance(ROOT)["totals"]
        rows = self.coverage["shards"]
        self.assertEqual(sum(row["matched"] for row in rows), totals["params_cell_matched"])
        self.assertEqual(sum(row["parameters"] for row in rows), totals["params_total"])

    def test_the_seven_are_concentrated_not_spread(self):
        """The distribution is the disclosure; the total was already published.

        Four shards hold every cell-matched parameter in the corpus and seven hold
        none. A reader told only "7 of 66" would reasonably assume the shortfall is
        spread evenly and that their shard carries some of it. For seven of eleven
        shards that is false.
        """
        c = self.coverage
        self.assertEqual(c["answering_own_cell"] + c["fully_bridged"], len(c["shards"]))
        self.assertGreater(c["fully_bridged"], c["answering_own_cell"],
                           "the shortfall is no longer concentrated; the disclosure needs rewording")

    def test_every_shard_reports_a_bridged_share_between_a_half_and_all(self):
        """The variance is the point: a corpus average would hide the worst shards."""
        for row in self.coverage["shards"]:
            self.assertGreaterEqual(row["bridged_share"], 0.5, row["id"])
            self.assertLessEqual(row["bridged_share"], 1.0, row["id"])
            self.assertEqual(row["bridged"] + row["matched"], row["parameters"], row["id"])


class DocumentFiguresTests(unittest.TestCase):
    """AGENTS.md: any number in public text is generated or pinned by a test.

    These figures were written into four documents on 2026-08-22 and every one of
    them is derived from the corpus, so every one of them can go stale silently. The
    rule was added in the same commit that introduced them; this is the rule being
    obeyed rather than merely stated.

    A failure here does not mean a document is wrong — it means the corpus moved and
    the prose did not. Fix the prose.
    """

    @classmethod
    def setUpClass(cls):
        shards = build_data(ROOT)["shards"]
        coverage = cell_coverage(shards)
        selves = shard_self_coverage(shards)
        split = answered_split(shards)
        matched = sum(row["matched"] for row in selves["shards"])
        total = sum(row["parameters"] for row in selves["shards"])
        cls.figures = {
            "cell_matched": f"{matched} of {total}",
            "answered": f"{split['answered']} of {coverage['combinations']}",
            "unpublished": f"{split['unpublished_cells']} of the {split['answered']}",
            "empty": str(coverage["empty"]),
            "traps": str(len(coverage["trap_pairs"])),
            "empty_share": f"{coverage['empty_share']:.1%}",
            "answering_own_cell": str(selves["answering_own_cell"]),
            "fully_bridged": str(selves["fully_bridged"]),
        }

    def _assert_states(self, relative, *keys):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for key in keys:
            self.assertIn(self.figures[key], text,
                          f"{relative} no longer states {key}={self.figures[key]!r}")

    def test_adr_0006_states_the_depth_measure_it_adopted(self):
        self._assert_states("docs/adr/0006-depth-over-breadth.md", "cell_matched")

    def test_adr_0016_states_the_boundary_figures(self):
        self._assert_states("docs/adr/0016-the-audit-is-the-product.md",
                            "cell_matched", "unpublished")

    def test_adr_0018_amendment_states_the_borrowed_floor(self):
        self._assert_states("docs/adr/0018-the-target-selector-failed-measurement.md",
                            "empty", "traps", "empty_share")

    def test_the_roadmap_states_what_both_tracks_rest_on(self):
        self._assert_states("docs/ROADMAP.md",
                            "cell_matched", "empty", "empty_share", "answered")


if __name__ == "__main__":
    unittest.main()
