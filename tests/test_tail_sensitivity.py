"""ADR-0008 commitment 2: how much of the answer rests on the maximum.

The load-bearing test here is `test_leverage_is_not_fiction`. Leverage is claimed as
an *analytic identity* rather than a simulated estimate, which is only legitimate while
the engine actually samples a beta-PERT at confidence 4. If someone changes the default
distribution, the identity silently becomes a lie on two public surfaces — so it is
pinned against the engine's own sampler rather than against itself.
"""
import random
import statistics
import unittest
from pathlib import Path

from engine.fair_calc import beta_pert
from engine.tail_sensitivity import (
    LEVERAGE_CONCERN,
    build_portfolio_tail_sensitivity,
    format_portfolio_markdown,
    headline,
    max_leverage,
    module_tail_sensitivity,
    pert_mean,
)

ROOT = Path(__file__).resolve().parents[1]


class LeverageMathTests(unittest.TestCase):
    def test_leverage_is_not_fiction(self):
        """The analytic mean must match what the engine's sampler actually produces.

        Tolerance is Monte Carlo error on 200k draws, not a fudge: if the distribution
        or its confidence parameter changes, this fails and the surfaces must be
        recomputed rather than quietly left wrong.
        """
        for low, likely, high in [
            (33_000, 170_000, 2_670_000),
            (1_000_000, 1_100_000, 76_000_000),
            (10, 20, 30),
        ]:
            rng = random.Random(42)
            empirical = statistics.fmean(
                beta_pert(low, likely, high, rng=rng) for _ in range(200_000)
            )
            analytic = pert_mean(low, likely, high)
            self.assertAlmostEqual(analytic / empirical, 1.0, delta=0.01, msg=(low, likely, high))

    def test_leverage_is_the_max_share_of_that_mean(self):
        impact = {"min": 33_000, "likely": 170_000, "max": 2_670_000}
        total = impact["min"] + 4 * impact["likely"] + impact["max"]
        self.assertAlmostEqual(max_leverage(impact), impact["max"] / total)
        # The three anchor contributions must account for the whole mean.
        self.assertAlmostEqual(
            (impact["min"] + 4 * impact["likely"]) / total + max_leverage(impact), 1.0
        )

    def test_a_degenerate_or_missing_range_does_not_raise(self):
        self.assertIsNone(max_leverage(None))
        self.assertIsNone(max_leverage({"min": 0, "likely": 0, "max": 0}))


class WorkedDecisionAgreementTests(unittest.TestCase):
    """This output generalises a hand computation; it must reproduce it.

    `docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md` reports the AU ransomware per-event
    mean as a multiple of its own mode. That number was computed by hand, in a document,
    before this module existed. If the module disagrees, one of them is wrong.

    It read 14.8x until 2026-08-23, when `impact.likely` was refreshed from the Sophos
    Australia 2025 country cut to the 2026 one. The mode tripled, the maximum did not
    move, and the ratio fell to 6.16x. **The document and this test were updated
    together**, which is the only way this check means anything.
    """

    def test_au_ransomware_mean_over_mode_matches_the_published_ratio(self):
        row = module_tail_sensitivity(ROOT, "au_finance_ransomware_midmarket")
        self.assertAlmostEqual(row["mean_over_mode"], 6.16, delta=0.01)


class PortfolioTailSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.portfolio = build_portfolio_tail_sensitivity(ROOT)

    def test_every_shard_reports_a_leverage_and_an_exceedance_basis(self):
        for row in self.portfolio["shards"]:
            self.assertIsNotNone(row["leverage"], row["module_id"])
            self.assertIsNotNone(row["exceedance_basis"], row["module_id"])

    def test_rows_are_ordered_most_tail_driven_first(self):
        levs = [r["leverage"] for r in self.portfolio["shards"]]
        self.assertEqual(levs, sorted(levs, reverse=True))

    def test_totals_agree_with_the_rows(self):
        t = self.portfolio["totals"]
        self.assertEqual(t["shards"], len(self.portfolio["shards"]))
        self.assertEqual(
            t["shards_majority_driven_by_max"],
            sum(1 for r in self.portfolio["shards"] if r["leverage"] >= LEVERAGE_CONCERN),
        )
        # The worrying subset can never exceed the set it is drawn from.
        self.assertLessEqual(
            t["shards_majority_driven_by_an_unquantified_max"],
            t["shards_majority_driven_by_max"],
        )

    def test_moving_only_the_maximum_moves_the_answer(self):
        """A swing that changes nothing would mean the stress is not being applied."""
        for row in self.portfolio["shards"]:
            halved = next(s for s in row["swings"] if s["factor"] == 0.5)
            doubled = next(s for s in row["swings"] if s["factor"] == 2.0)
            self.assertLess(halved["avg_change"], 0, row["module_id"])
            self.assertGreater(doubled["avg_change"], 0, row["module_id"])
            # Direction and rough size should track leverage: a shard whose mean is
            # mostly its maximum must move more than one whose mean barely is.
            self.assertAlmostEqual(
                doubled["avg_change"], row["leverage"], delta=0.05, msg=row["module_id"]
            )

    def test_markdown_carries_the_headline_and_a_row_per_shard(self):
        markdown = format_portfolio_markdown(self.portfolio)
        self.assertIn("Tail sensitivity report", markdown)
        self.assertIn(headline(self.portfolio["totals"]), markdown)
        for row in self.portfolio["shards"]:
            self.assertIn(f"`{row['module_id']}`", markdown)


class PublishedSurfaceTests(unittest.TestCase):
    """Commitment 2 exists because commitment 1's lesson was that CLI-only reaches nobody."""

    def test_evidence_report_calls_out_every_tail_driven_shard(self):
        from engine.provenance import build_portfolio_provenance, format_portfolio_markdown as report

        markdown = report(build_portfolio_provenance(ROOT))
        expected = build_portfolio_tail_sensitivity(ROOT)["totals"]["shards_majority_driven_by_max"]
        self.assertEqual(markdown.count("comes from `impact.max` alone"), expected)

    def test_explorer_payload_carries_leverage_per_shard_and_in_totals(self):
        from scripts.build_explorer import build_data

        data = build_data(ROOT)
        self.assertIn("shards_tail_driven", data["totals"])
        for shard in data["shards"]:
            self.assertIsNotNone(shard.get("leverage"), shard["id"])
        self.assertEqual(
            data["totals"]["shards_tail_driven"],
            sum(1 for s in data["shards"] if s["leverage"] >= LEVERAGE_CONCERN),
        )

    def test_explorer_template_renders_the_leverage_note_and_the_paragraph(self):
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        # Indentation moved when the note was nested inside the reference-rendering
        # block: it is a caveat on the loss figure, so it travels with it.
        self.assertIn("comes from '+\n           'the maximum alone", template)
        # The long-form basis moved to docs/BASIS_OF_PREPARATION.md in the 2026-08-19
        # density cut. The caveat itself did NOT move: the front page must still say,
        # in its own words, that the maximum drives the average rather than capping
        # it, and that a figure past the halfway share says so on its face.
        # "Caveats get louder, not quieter" is a rule about the page a reader lands
        # on, so moving this behind a link would have been a real loss.
        self.assertIn("drives the modeled average\n    rather than capping it", template)
        self.assertIn("Where its share exceeds half, the item says so", template)

    def test_the_long_form_tail_caveat_survives_the_move(self):
        """The compressed front-page version must still have a full version to reach.

        A caveat cut down to one sentence with nowhere to expand is a caveat that
        quietly lost its reasoning, so the destination is pinned too.
        """
        basis = (ROOT / "docs" / "BASIS_OF_PREPARATION.md").read_text(encoding="utf-8")
        self.assertIn("The maximum drives the average rather than capping it", basis)
        self.assertIn("resting on one observation", basis)
        self.assertIn("the largest loss found", basis)
        # and the front page has to link to it, or the move stranded the reader
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        self.assertIn("docs/BASIS_OF_PREPARATION.md", template)


if __name__ == "__main__":
    unittest.main()
