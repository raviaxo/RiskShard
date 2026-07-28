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
        self.assertTrue(revisions, "revisions.yaml should carry the ADR-0002 entry")
        first = revisions[0]
        for field in ("date", "title", "effect", "reason"):
            self.assertTrue(first[field], f"revision entry missing {field}")

        sample = dict(SAMPLE, revisions=revisions)
        html = render(sample)
        self.assertIn("Why these figures changed", html)
        self.assertIn(first["title"], html)

    def test_layers_are_deep_linkable(self):
        """A number under discussion has to be addressable on its own."""
        html = render(SAMPLE)
        self.assertIn("applyHash", html)
        self.assertIn("hashchange", html)
        self.assertIn('data-param="', html)
        self.assertIn("copy link to this layer", html)


if __name__ == "__main__":
    unittest.main()
