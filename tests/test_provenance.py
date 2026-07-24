import unittest
from pathlib import Path

from engine.provenance import (
    build_dispute_issue,
    build_module_provenance,
    build_portfolio_provenance,
    dispute_issue_url,
    format_portfolio_markdown,
    format_provenance,
    repo_slug_from_remote,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE = "gb_finance_data_breach_midmarket"


class RepoSlugTests(unittest.TestCase):
    def test_parses_https_and_ssh_and_strips_git(self):
        self.assertEqual(repo_slug_from_remote("https://github.com/raviaxo/RiskShard.git"), "raviaxo/RiskShard")
        self.assertEqual(repo_slug_from_remote("git@github.com:raviaxo/RiskShard.git"), "raviaxo/RiskShard")
        self.assertEqual(repo_slug_from_remote(""), "")


class ProvenanceCardTests(unittest.TestCase):
    def setUp(self):
        self.prov = build_module_provenance(MODULE, ROOT)

    def test_one_card_per_direct_parameter(self):
        params = [c["parameter"] for c in self.prov["cards"]]
        self.assertEqual(len(params), 6)
        self.assertIn("frequency.min", params)
        self.assertIn("impact.max", params)

    def test_card_carries_value_source_quote_and_caveat(self):
        card = next(c for c in self.prov["cards"] if c["parameter"] == "frequency.min")
        self.assertTrue(card["resolved"])
        self.assertIsNotNone(card["value"])
        self.assertTrue(card["source_name"])
        self.assertTrue(card["cited_line"])       # the exact quote
        self.assertTrue(card["caveat"])           # the limitation, surfaced not hidden

    def test_format_single_parameter_shows_all_fields(self):
        out = format_provenance(self.prov, parameter="frequency.min")
        for label in ("Source :", "Cite   :", "Quote  :", "Caveat :"):
            self.assertIn(label, out)

    def test_format_unknown_parameter_is_graceful(self):
        out = format_provenance(self.prov, parameter="nonsense.param")
        self.assertIn("No such parameter", out)


class DisputeIssueTests(unittest.TestCase):
    def setUp(self):
        self.prov = build_module_provenance(MODULE, ROOT)

    def test_dispute_issue_names_the_parameter_and_current_state(self):
        issue = build_dispute_issue(self.prov, "impact.max")
        self.assertIn("impact.max", issue["title"])
        self.assertIn(MODULE, issue["body"])
        self.assertIn("What I'm disputing", issue["body"])
        self.assertIn("Evidence I'm proposing instead", issue["body"])

    def test_dispute_unknown_parameter_raises(self):
        with self.assertRaises(ValueError):
            build_dispute_issue(self.prov, "no.such")

    def test_dispute_url_is_prefilled_new_issue(self):
        issue = build_dispute_issue(self.prov, "impact.max")
        url = dispute_issue_url("raviaxo/RiskShard", issue)
        self.assertTrue(url.startswith("https://github.com/raviaxo/RiskShard/issues/new?"))
        self.assertIn("title=", url)
        self.assertIn("body=", url)

    def test_dispute_url_falls_back_to_default_slug(self):
        issue = build_dispute_issue(self.prov, "impact.max")
        url = dispute_issue_url("", issue)
        self.assertIn("github.com/raviaxo/RiskShard/issues/new", url)


class PortfolioProvenanceTests(unittest.TestCase):
    def setUp(self):
        # Scope to two shards for speed; totals still exercise the counting logic.
        self.portfolio = build_portfolio_provenance(
            ROOT, module_ids=[MODULE, "jp_manufacturing_ransomware_midmarket"]
        )

    def test_totals_count_parameters_by_status(self):
        t = self.portfolio["totals"]
        self.assertEqual(t["shards"], 2)
        self.assertEqual(t["params_total"], 12)          # 6 per shard
        # Both GB and JP are now 6/6 source-backed (JP closed 2026-07-24)
        self.assertEqual(t["params_source_backed"], 12)
        self.assertEqual(t["params_bridged"], 0)
        self.assertEqual(t["params_missing"], 0)

    def test_markdown_report_shows_totals_and_a_param_row(self):
        md = format_portfolio_markdown(self.portfolio)
        self.assertIn("# RiskShard Evidence Report", md)
        self.assertIn("12 of 12 parameters source-backed", md)
        self.assertIn("| `frequency.min` |", md)

    def test_markdown_flags_bridged_rows_when_present(self):
        # Synthetic portfolio: the report must SHOW bridged rows, not hide them.
        synthetic = {
            "totals": {"shards": 1, "params_total": 2, "params_source_backed": 1,
                       "params_bridged": 1, "params_missing": 0},
            "modules": [{
                "module_id": "demo_shard",
                "title": "Demo",
                "cards": [
                    {"parameter": "frequency.min", "status": "source_backed", "value": 0.1,
                     "unit": "annual_probability", "source_name": "Some Source",
                     "publication_date": "2025-01-01", "caveat": "a caveat", "resolved": True},
                    {"parameter": "frequency.max", "status": "assumption_only", "value": 0.5,
                     "unit": "annual_probability", "source_name": "Starter pack",
                     "publication_date": None, "caveat": "not source-backed", "resolved": True},
                ],
            }],
        }
        md = format_portfolio_markdown(synthetic)
        self.assertIn("1 of 2 parameters source-backed", md)
        self.assertIn("assumption_only", md)             # bridged rows shown, not hidden


if __name__ == "__main__":
    unittest.main()
