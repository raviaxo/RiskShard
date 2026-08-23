import unittest

import os
import stat
import tempfile
from pathlib import Path

from scripts.build_social_card import (DEFAULT_HEADLINE, _month_year, default_outcome,
                                       main, money, rasterise, render)


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


class RasteriseTests(unittest.TestCase):
    """Success is whether the file was written, not what Chrome's exit status said.

    On the maintainer's machine a normal Chrome of the same channel is usually already
    open, and headless Chrome then writes the screenshot and exits non-zero anyway. The
    earlier version read that as failure and printed "Headless Chrome did not produce a
    PNG" over a card it had just correctly regenerated. A build step that cries wolf
    about a stale public asset trains everyone to ignore it, and the next staleness is
    real — this is the same card whose coverage line has already gone stale twice.
    """

    def _fake_chrome(self, directory, script):
        path = Path(directory) / "fake-chrome"
        path.write_text("#!/bin/sh\n" + script, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return str(path)

    def test_a_written_png_counts_even_when_chrome_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as d:
            png = Path(d) / "card.png"
            html = Path(d) / "card.html"
            html.write_text("<p>card</p>", encoding="utf-8")
            png.write_bytes(b"stale")
            os.utime(png, (1, 1))
            chrome = self._fake_chrome(d, 'printf new > "$(echo "$@" | sed -n '
                                          '"s/.*--screenshot=\\([^ ]*\\).*/\\1/p")"\nexit 1\n')
            self.assertTrue(rasterise(html, png, chrome, timeout=30))
            self.assertEqual(png.read_bytes(), b"new")

    def test_an_untouched_png_is_still_a_failure(self):
        """The fix must not turn every failure into a success: if Chrome writes
        nothing, a stale card on disk is exactly what we need to hear about."""
        with tempfile.TemporaryDirectory() as d:
            png = Path(d) / "card.png"
            html = Path(d) / "card.html"
            html.write_text("<p>card</p>", encoding="utf-8")
            png.write_bytes(b"stale")
            os.utime(png, (1, 1))
            chrome = self._fake_chrome(d, "exit 1\n")
            self.assertFalse(rasterise(html, png, chrome, timeout=30))
            self.assertEqual(png.read_bytes(), b"stale")


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

