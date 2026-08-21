import unittest

from scripts.build_social_card import (DEFAULT_HEADLINE, _month_year, default_outcome,
                                       main, money, render)


FIELDS = {
    "__RS_HEADLINE__": "A headline with <em>emphasis.</em>",
    "__RS_OUTCOME__": "An outcome line.",
    "__RS_SPEC__": "US · FINANCIAL SERVICES · MID-MARKET · BUSINESS EMAIL COMPROMISE",
    "__RS_PARAM__": "impact.likely",
    "__RS_VALUE__": "$123,005",
    "__RS_SOURCE__": "FBI IC3 2025 Annual Report · Apr 2026",
    "__RS_TAG__": "✓ verified",
    "__RS_TAGCLASS__": "",
    "__RS_SHARDS__": "11",
    "__RS_BACKED__": "66 / 66",
    "__RS_COUNTRIES__": "8",
    "__RS_URL__": "raviaxo.github.io/RiskShard",
}


class RenderTests(unittest.TestCase):
    def test_render_fills_every_placeholder(self):
        markup = render(dict(FIELDS))
        self.assertTrue(markup.lstrip().startswith("<!doctype"))
        for token in FIELDS:
            self.assertNotIn(token, markup)
        self.assertIn("$123,005", markup)
        self.assertIn("FBI IC3 2025 Annual Report · Apr 2026", markup)

    def test_money_renders_whole_currency_units(self):
        self.assertEqual(money(123005.43), "$123,005")
        self.assertEqual(money(50000), "$50,000")

    def test_month_year_is_human_readable(self):
        self.assertEqual(_month_year("2026-04-16"), "Apr 2026")
        self.assertEqual(_month_year("nonsense"), "nonsense")


class DriftTests(unittest.TestCase):
    def test_committed_card_matches_live_repo_data(self):
        """The card is what people see when a link is shared — it must not go stale."""
        self.assertEqual(main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()


class CardCarriesTheCurrentMessageTests(unittest.TestCase):
    """The card is the first thing a reader sees on a shared link.

    It shipped from 2026-08-07 to 2026-08-19 reading "Tell your CEO what it costs"
    over "cyber risk as a defensible dollar range", which is the simulation-as-product
    framing ADR-0010 retired and ADR-0016 replaced. Nothing caught it, because nothing
    was looking: the card had tests for its rendering and none for its claim. So it
    contradicted the page it linked to for twelve days.
    """

    RETIRED = ("tell your ceo", "defensible dollar range", "instead of another red square",
               "library of defensible", "benchmarked risk parameters")

    def test_the_default_card_does_not_carry_a_retired_framing(self):
        text = (DEFAULT_HEADLINE + " " + default_outcome()).lower()
        for phrase in self.RETIRED:
            self.assertNotIn(phrase, text, f"the card is selling a retired framing: {phrase!r}")

    def test_the_default_card_leads_with_the_audit(self):
        text = (DEFAULT_HEADLINE + " " + default_outcome()).lower()
        self.assertIn("mode", text)

    def test_the_cards_coverage_is_generated_not_typed(self):
        """It was typed, and went stale twice in three days as the audit moved.

        A stale denominator on the image attached to a shared link is the exact
        failure this project argues against, so the assertion is against the engine
        rather than against a literal a future edit would have to remember.
        """
        from engine.source_audit import build_source_audit
        from engine.project_paths import find_project_root

        coverage = build_source_audit(find_project_root())["coverage"]
        self.assertIn(
            f"{coverage['sources_fully_verified']} of {coverage['sources']}",
            default_outcome(),
        )

