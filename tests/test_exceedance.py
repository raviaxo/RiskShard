"""ADR-0008: a maximum must say what it bounds.

Mirrors test_coherence.py. The declaration tests pin the field to the data, the
measurement tests pin the portfolio fact, and the surface tests pin it to the two
places a reader actually meets — the lesson ADR-0003 and ADR-0007 both learned the
hard way: a caveat only counts where it is published.
"""
import glob
import json
import re
import unittest
from pathlib import Path

import yaml

from engine.exceedance import (
    BASES,
    QUANTIFIED,
    build_portfolio_exceedance,
    format_portfolio_markdown,
    headline,
    module_exceedance,
)
from engine.provenance import build_module_provenance

ROOT = Path(__file__).resolve().parents[1]
IMPACT_MAX = re.compile(r"(^|\.)impact\.max$")


def _schema_vocabulary(field):
    schema = json.loads((ROOT / "schemas" / "evidence_record_schema.json").read_text(encoding="utf-8"))
    return set(schema["properties"]["records"]["items"]["properties"][field]["enum"])


class ExceedanceDeclarationTests(unittest.TestCase):
    """Part 1: every record anchoring an impact maximum declares an exceedance basis."""

    def setUp(self):
        self.records = []
        for path in sorted(glob.glob(str(ROOT / "evidence" / "*.yaml"))):
            payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
            for record in payload.get("records", []):
                self.records.append((Path(path).name, record))

    def _maxima(self):
        return [
            (name, r) for name, r in self.records if IMPACT_MAX.search(r.get("parameter") or "")
        ]

    def test_the_repo_actually_has_maxima_to_check(self):
        # Guards the suite itself: a regex that silently stopped matching would make
        # every other test in this class vacuously pass.
        self.assertGreaterEqual(len(self._maxima()), 11)

    def test_every_impact_max_declares_an_exceedance_basis(self):
        missing = [
            f"{name}:{r.get('id')}" for name, r in self._maxima() if not r.get("exceedance_basis")
        ]
        self.assertEqual(missing, [], f"impact maxima without an exceedance_basis: {missing}")

    def test_declared_bases_are_in_the_schema_vocabulary(self):
        allowed = _schema_vocabulary("exceedance_basis")
        self.assertEqual(allowed, set(BASES))
        bad = [
            f"{name}:{r.get('id')}={r.get('exceedance_basis')}"
            for name, r in self._maxima()
            if r.get("exceedance_basis") not in allowed
        ]
        self.assertEqual(bad, [])

    def test_a_quantified_claim_carries_its_statement(self):
        """`modeled_quantile` / `observed_rank` without the number is an empty claim."""
        empty = [
            f"{name}:{r.get('id')}"
            for name, r in self._maxima()
            if r.get("exceedance_basis") in QUANTIFIED and not r.get("exceedance_detail")
        ]
        self.assertEqual(empty, [])

    def test_nothing_but_a_maximum_declares_an_exceedance_basis(self):
        """The field is meaningless on a floor or a mode; a stray one is a modeling error."""
        stray = [
            f"{name}:{r.get('id')}"
            for name, r in self.records
            if r.get("exceedance_basis") and not IMPACT_MAX.search(r.get("parameter") or "")
        ]
        self.assertEqual(stray, [])


class PortfolioExceedanceTests(unittest.TestCase):
    """Part 2: the portfolio fact is measured, not asserted."""

    @classmethod
    def setUpClass(cls):
        cls.portfolio = build_portfolio_exceedance(ROOT)

    def test_every_shard_has_exactly_one_impact_maximum(self):
        for module in self.portfolio["modules"]:
            self.assertEqual(len(module["maxima"]), 1, module["module_id"])

    def test_no_selected_maximum_is_left_undeclared(self):
        self.assertEqual(self.portfolio["totals"]["undeclared"], 0)

    def test_totals_are_internally_consistent(self):
        t = self.portfolio["totals"]
        self.assertEqual(sum(t["by_basis"].values()), t["maxima"])
        self.assertEqual(t["quantified"], sum(t["by_basis"][b] for b in QUANTIFIED))

    def test_the_adr_0008_claim_still_holds(self):
        """No maximum in this portfolio is a modeled quantile.

        This is the load-bearing sentence of ADR-0008 and of the README front door.
        If a modeled quantile ever lands, that is excellent news and this test should
        be updated deliberately — not a reason to quietly reword the claim.
        """
        self.assertEqual(self.portfolio["totals"]["by_basis"]["modeled_quantile"], 0)

    def test_a_module_view_matches_the_portfolio(self):
        module = build_module_provenance("us_finance_data_breach_midmarket", ROOT)
        maxima = module_exceedance(module)
        self.assertEqual(len(maxima), 1)
        self.assertEqual(maxima[0]["exceedance_basis"], "observed_rank")
        self.assertTrue(maxima[0]["quantified"])
        self.assertIn("579", maxima[0]["exceedance_detail"])

    def test_markdown_warns_on_every_unquantified_maximum(self):
        markdown = format_portfolio_markdown(self.portfolio)
        self.assertIn("Tail exceedance report", markdown)
        self.assertIn(headline(self.portfolio["totals"]), markdown)
        none_known = self.portfolio["totals"]["by_basis"]["none_known"]
        self.assertEqual(markdown.count("carries no exceedance probability"), none_known)


class PublishedSurfaceTests(unittest.TestCase):
    """Part 3: it reaches a reader, or it does not count."""

    def test_evidence_report_carries_the_headline_a_column_and_a_callout(self):
        from engine.provenance import build_portfolio_provenance, format_portfolio_markdown as report

        markdown = report(build_portfolio_provenance(ROOT))
        self.assertIn("**Tail exceedance:**", markdown)
        self.assertIn("| Parameter | Value | Status | Measures | Exceedance | Source | Caveat |", markdown)
        self.assertIn("bounds nothing", markdown)
        self.assertIn("`none_known`", markdown)

    def test_explorer_payload_carries_exceedance_per_row_and_in_totals(self):
        from scripts.build_explorer import build_data

        data = build_data(ROOT)
        totals = data["totals"]
        for key in ("maxima", "maxima_quantified", "maxima_none_known"):
            self.assertIn(key, totals)
        self.assertEqual(totals["maxima"], len(data["shards"]))

        declared = [
            p
            for s in data["shards"]
            for p in s["params"]
            if p.get("exceedance")
        ]
        self.assertEqual(len(declared), totals["maxima"])
        self.assertTrue(all(p["parameter"].endswith("impact.max") for p in declared))

        us_db = next(s for s in data["shards"] if s["id"] == "us_finance_data_breach_midmarket")
        mx = next(p for p in us_db["params"] if p["parameter"] == "impact.max")
        self.assertEqual(mx["exceedance"], "observed_rank")
        self.assertIn("579", mx["exceedance_detail"])

    def test_explorer_template_renders_the_exceedance_line_and_the_note(self):
        template = (ROOT / "scripts" / "explorer_template.html").read_text(encoding="utf-8")
        self.assertIn("exceedance", template)
        self.assertIn("A maximum on this page is not a bound", template)
        self.assertIn("largest loss found", template)


if __name__ == "__main__":
    unittest.main()
