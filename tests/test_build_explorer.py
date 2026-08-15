import json
import unittest

from scripts.build_explorer import render


SAMPLE = {
    "totals": {"shards": 1, "params_total": 6, "params_source_backed": 6,
               "params_bridged": 0, "params_missing": 0},
    "shards": [{
        "id": "xx_demo", "title": "Demo", "country": "XX", "industry": "finance",
        "size": "mid_market", "threat": "data_breach", "status": "governed_starter",
        "avg": "USD 1,000", "p95": "USD 2,000", "p99": "USD 3,000",
        "params": [{"parameter": "frequency.min", "value": 0.1, "unit": "annual_probability",
                    "status": "source_backed", "confidence": "medium", "source_name": "Src",
                    "source_type": "survey", "publication_date": "2025-01-01",
                    "quote": "a line", "caveat": "a caveat"}],
    }],
    "repo": "https://github.com/raviaxo/RiskShard",
}


class RenderTests(unittest.TestCase):
    def test_render_is_a_full_document_with_data_injected(self):
        html = render(SAMPLE)
        self.assertTrue(html.lstrip().startswith("<!doctype"))
        self.assertIn("</body>", html)
        self.assertNotIn("__RS_DATA__", html)
        # the embedded JSON round-trips
        start = html.index('id="rs-data">') + len('id="rs-data">')
        end = html.index("</script>", start)
        data = json.loads(html[start:end])
        self.assertEqual(data["totals"]["params_source_backed"], 6)
        self.assertEqual(data["shards"][0]["id"], "xx_demo")

    def test_render_refuses_data_that_would_break_out_of_the_script_tag(self):
        bad = {"totals": {}, "shards": [{"id": "</script><script>alert(1)"}], "repo": "x"}
        with self.assertRaises(ValueError):
            render(bad)

    def test_link_previews_carry_absolute_urls(self):
        """Shared links must render a card, so og:/twitter: URLs cannot be relative."""
        html = render(SAMPLE, site_url="https://example.test/RiskShard/")
        self.assertNotIn("__RS_SITE__", html)
        for tag in (
            '<meta property="og:url" content="https://example.test/RiskShard/">',
            '<meta property="og:image" content="https://example.test/RiskShard/social-card.png">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<link rel="canonical" href="https://example.test/RiskShard/">',
        ):
            self.assertIn(tag, html)

    def test_revisions_explain_why_a_published_number_moved(self):
        """A returning reader must be able to see a figure changed, and why."""
        from scripts.build_explorer import load_revisions

        revisions = load_revisions()
        self.assertTrue(revisions, "revisions/ should carry the ADR-0002 entry")
        # every entry, not just the first: these render publicly, and a missing field
        # shows as blank text on the live page rather than failing the build
        for entry in revisions:
            for field in ("date", "title", "effect", "reason"):
                self.assertTrue(entry[field], f"{entry.get('title')!r} missing {field}")
        self.assertEqual(revisions, sorted(revisions, key=lambda e: e["date"], reverse=True))

        sample = dict(SAMPLE, revisions=revisions)
        html = render(sample)
        self.assertIn("Why these figures changed", html)
        self.assertIn(revisions[0]["title"], html)

    def test_the_front_door_discloses_that_its_headline_count_moved(self):
        """A count that halves on unchanged evidence must say so where it is read.

        The cell-matched headline went 31 -> 7 on 2026-08-15 with no parameter,
        source, value or caveat touched, because fit stopped being an authored field
        and became a computed one (ADR-0013). The README and the evidence report both
        carry that correction; this page is the one most people actually see, so a
        reader arriving at "7 cell-matched" must be able to learn why here rather
        than by opening the changelog.

        Pins the disclosure, deliberately not the digits — the live counts are
        rendered from DATA.totals and will move again.
        """
        html = render(SAMPLE)
        for phrase in ("2026-08-15", "45 of 66", "No published figure moved"):
            self.assertIn(phrase, html, f"front door no longer discloses: {phrase}")
        # the consequence a reader needs while reading the rows themselves
        self.assertIn("statutory penalty cap", html)

    def test_citations_pin_to_an_immutable_release(self):
        """ADR-0004: a cited figure must still resolve to the value that was cited."""
        from scripts.build_explorer import latest_release

        release = latest_release()
        self.assertTrue(release, "a data-pack release is needed to pin citations")

        html = render(dict(SAMPLE, release=release, site="https://example.test/RiskShard/"))
        self.assertIn("cite this number", html)
        self.assertIn("paramID", html)
        # the pinned form, not just the canonical one
        self.assertIn("'@'+RELEASE", html)

    def test_renamed_shards_keep_resolving(self):
        """A rename must not break a citation someone already wrote down."""
        from scripts.build_explorer import load_aliases

        self.assertIsInstance(load_aliases(), dict)
        html = render(SAMPLE)
        self.assertIn("DATA.aliases", html)

    def test_archived_copy_reaches_shared_assets(self):
        """An archive under docs/r/<release>/ must not ship duplicate fonts."""
        archived = render(SAMPLE, asset_prefix="../../")
        self.assertIn('url("../../fonts/plex-mono-400.woff2")', archived)
        self.assertNotIn('url("fonts/', archived)

        current = render(SAMPLE)
        self.assertIn('url("fonts/plex-mono-400.woff2")', current)

    def test_layers_are_deep_linkable(self):
        """A number under discussion has to be addressable on its own."""
        html = render(SAMPLE)
        self.assertIn("applyHash", html)
        self.assertIn("hashchange", html)
        self.assertIn('data-param="', html)
        self.assertIn("copy link to this layer", html)


if __name__ == "__main__":
    unittest.main()
