import unittest
from pathlib import Path

from engine.provenance import (
    build_dispute_issue,
    build_module_provenance,
    dispute_issue_url,
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


if __name__ == "__main__":
    unittest.main()
