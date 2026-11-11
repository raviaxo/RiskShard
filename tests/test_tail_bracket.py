"""The published-distribution bracket, and the prose that reports it.

Two jobs. The first is the engine: Table 1 parses out of its committed extract,
tier boundaries land where the source's own labels put them, and the bracket
classification is right at the edges. The second is the one this repo keeps
learning it needs — `docs/FINDINGS.md` states counts in prose, and a number typed
into prose has no owner and nothing watching it. Finding 12's figures are checked
against the live computation here, so the document cannot drift from the engine.
"""

import re
import unittest
from pathlib import Path

from engine.tail_bracket import (
    BRACKET_MEANING,
    TIER_BOUNDS,
    _bracket,
    build_portfolio_brackets,
    load_tiers,
    tier_for_revenue,
)

ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "docs" / "FINDINGS.md"


class TableExtractTests(unittest.TestCase):
    def test_all_four_published_tiers_parse(self):
        tiers = load_tiers(ROOT / "extractions"
                           / "cyentia_iris_2025_table1_loss_percentiles.txt")
        self.assertEqual(set(tiers), set(TIER_BOUNDS))

    def test_the_two_tiers_our_profiles_occupy_carry_the_published_figures(self):
        tiers = load_tiers(ROOT / "extractions"
                           / "cyentia_iris_2025_table1_loss_percentiles.txt")
        self.assertEqual(tiers["Less than $100M"], {50: 357_000.0, 95: 9_100_000.0})
        self.assertEqual(tiers["$100M to $1B"], {50: 466_700.0, 95: 12_300_000.0})

    def test_a_truncated_extract_fails_loudly(self):
        """Silently losing a row would shrink the table rather than break it."""
        import tempfile
        full = (ROOT / "extractions"
                / "cyentia_iris_2025_table1_loss_percentiles.txt").read_text()
        cut = "\n".join(l for l in full.splitlines() if "Less than $100M" not in l)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write(cut)
        with self.assertRaises(ValueError):
            load_tiers(handle.name)


class TierBoundaryTests(unittest.TestCase):
    def test_our_profile_revenues_land_in_the_tiers_the_labels_state(self):
        self.assertEqual(tier_for_revenue(85_000_000), "Less than $100M")
        self.assertEqual(tier_for_revenue(90_000_000), "Less than $100M")
        self.assertEqual(tier_for_revenue(120_000_000), "$100M to $1B")
        self.assertEqual(tier_for_revenue(130_000_000), "$100M to $1B")

    def test_the_boundary_itself_goes_to_the_upper_tier(self):
        self.assertEqual(tier_for_revenue(100_000_000), "$100M to $1B")
        self.assertEqual(tier_for_revenue(99_999_999), "Less than $100M")


class BracketTests(unittest.TestCase):
    TIER = {50: 357_000.0, 95: 9_100_000.0}

    def test_classification_at_and_around_the_edges(self):
        self.assertEqual(_bracket(9_100_001, self.TIER), "above_p95")
        self.assertEqual(_bracket(9_100_000, self.TIER), "between_p50_p95")
        self.assertEqual(_bracket(357_000, self.TIER), "between_p50_p95")
        self.assertEqual(_bracket(356_999, self.TIER), "below_p50")

    def test_every_bracket_tells_a_reader_what_it_licenses(self):
        for name in ("above_p95", "between_p50_p95", "below_p50"):
            self.assertIn(name, BRACKET_MEANING)
            self.assertRegex(BRACKET_MEANING[name], r"%|half")


class PortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build_portfolio_brackets(ROOT)

    def test_every_published_maximum_is_placed_none_skipped(self):
        skipped = [m["module_id"] for m in self.result["modules"] if m["bracket"] is None]
        self.assertEqual(skipped, [], f"unplaced maxima: {skipped}")

    def test_a_currency_anchor_is_converted_and_discloses_its_rate(self):
        """AU anchors are held in AUD; the comparison is only honest in USD."""
        au = next(m for m in self.result["modules"]
                  if m["module_id"] == "au_finance_ransomware_midmarket")
        self.assertEqual(au["currency"], "AUD")
        self.assertIsNotNone(au["fx_rate_id"])
        self.assertNotEqual(au["usd"], au["value"])


class FindingProseTests(unittest.TestCase):
    """Finding 12's numbers are generated, not typed. This is what enforces it."""

    @classmethod
    def setUpClass(cls):
        cls.result = build_portfolio_brackets(ROOT)
        cls.text = FINDINGS.read_text(encoding="utf-8")
        cls.finding = cls.text.split("### 12 —")[-1].split("\n### ")[0]

    def test_finding_12_exists(self):
        self.assertIn("### 12 —", self.text)

    def test_the_headline_count_matches_the_live_computation(self):
        at_or_below = self.result["totals"]["at_or_below_p95"]
        placed = self.result["totals"]["placed"]
        self.assertRegex(
            self.finding,
            rf"\*\*{at_or_below} of {placed}\*\*",
            f"finding 12 must state {at_or_below} of {placed} at or below the 95th",
        )

    def test_every_shard_row_states_the_ratio_the_engine_computes(self):
        rows = dict(re.findall(
            r"`([a-z0-9_]+)`[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^*]*\*\*([0-9.]+)×\*\*",
            self.finding))
        self.assertTrue(rows, "finding 12 must carry a per-shard table with ratios")
        for module in self.result["modules"]:
            stated = rows.get(module["module_id"])
            if stated is None:
                continue
            self.assertEqual(
                stated, f"{module['ratio_to_p95']:.2f}",
                f"{module['module_id']}: finding says {stated}×, "
                f"engine computes {module['ratio_to_p95']:.2f}×",
            )

    def test_the_retired_claim_is_not_still_asserted_anywhere(self):
        """Finding 3 said no such distribution had been found, publicly, anywhere."""
        self.assertNotIn("We have not found one, publicly, anywhere", self.text)


if __name__ == "__main__":
    unittest.main()
