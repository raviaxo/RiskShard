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


if __name__ == "__main__":
    unittest.main()
