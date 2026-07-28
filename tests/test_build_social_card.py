import unittest

from scripts.build_social_card import _month_year, main, money, render


FIELDS = {
    "__RS_HEADLINE__": "Tell your CEO what it <em>costs.</em>",
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
