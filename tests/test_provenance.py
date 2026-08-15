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


class PopulationMatchTests(unittest.TestCase):
    """ADR-0003: the headline splits cell-matched from bridged, and the split is honest."""

    def test_card_population_is_country_strict(self):
        from engine.provenance import _card_population

        # A record that names the shard's country and is population-matched: cell-matched.
        record = {"population_match": {"status": "matched"},
                  "applicability": {"countries": ["GB"]}}
        self.assertEqual(_card_population(record, "GB")["status"], "matched")

        # A global survey consumed by a concrete cell is bridged on country,
        # whatever it honestly declared.
        record = {"population_match": {"status": "matched"},
                  "applicability": {"countries": ["global"]}}
        pop = _card_population(record, "AU")
        self.assertEqual(pop["status"], "bridged")
        self.assertIn("country", pop["bridged_on"])

        # Stored over-claims survive into the card even when the country matches.
        record = {"population_match": {"status": "bridged", "bridged_on": ["sector", "size"]},
                  "applicability": {"countries": ["US"]}}
        pop = _card_population(record, "US")
        self.assertEqual(pop["status"], "bridged")
        self.assertEqual(pop["bridged_on"], ["sector", "size"])

    def test_cards_display_the_record_the_calibration_selects(self):
        # The invariant behind the challenge affordance: the record a card shows
        # must be the record the simulation uses. Found violated 2026-08-02 when a
        # superseded record kept "for reference" outranked the calibration's
        # selection in the pack's confidence-then-id ordering. Checked repo-wide:
        # every card of every shard whose calibration names an evidence_id for
        # that parameter must display exactly that record.
        from engine.provenance import _calibration_selected_evidence
        from engine.risk_modules import load_risk_modules

        for module in load_risk_modules(ROOT):
            selected = _calibration_selected_evidence(module, ROOT)
            if not selected:
                continue
            prov = build_module_provenance(module["id"], ROOT)
            for card in prov["cards"]:
                expected = selected.get(card["parameter"])
                if expected:
                    self.assertEqual(
                        card["evidence_id"],
                        expected,
                        f"{module['id']}/{card['parameter']} displays "
                        f"{card['evidence_id']} but the calibration selects {expected}",
                    )

    def test_portfolio_totals_split_and_sum(self):
        from pathlib import Path

        totals = build_portfolio_provenance(Path(__file__).resolve().parents[1])["totals"]
        self.assertEqual(
            totals["params_cell_matched"] + totals["params_cross_cell"],
            totals["params_source_backed"],
        )
        self.assertLessEqual(totals["params_cross_country"], totals["params_cross_cell"])
        # The split exists to be able to fall: bridged must be visible, not zeroed.
        self.assertGreater(totals["params_cross_cell"], 0)


class TargetRelativeFitTests(unittest.TestCase):
    """ADR-0011: fit is computed against a target, and the target is always named.

    The failure these guard against is a derived, target-specific value reading as
    an intrinsic property of the record — and its mirror image, an intrinsic
    property reading as target-relative.
    """

    def setUp(self):
        self.prov = build_module_provenance(MODULE, ROOT)

    def test_module_provenance_names_the_cell_fit_is_computed_against(self):
        cell = self.prov["cell"]
        self.assertEqual(cell["country"], "GB")
        for key in ("country", "industry", "company_size", "threat"):
            self.assertTrue(cell.get(key), f"cell is missing {key}")

    def test_every_resolved_card_carries_both_declarations(self):
        for card in self.prov["cards"]:
            if not card.get("resolved"):
                continue
            declared = card["declared_for"]
            for facet in ("countries", "industries", "company_size_bands", "threats"):
                self.assertTrue(declared.get(facet), f"{card['parameter']} declares no {facet}")
            self.assertIsInstance(card["not_measured_on"], list)

    def test_cell_mismatch_is_only_the_target_relative_half(self):
        from engine.provenance import cell_mismatch

        # Stored `bridged_on` is a property of the record: the source measured a
        # broader population than the record declares. It is true for every reader
        # and must not be reported as a mismatch against our cell.
        card = {"population": {"status": "bridged", "bridged_on": ["sector", "size"]},
                "not_measured_on": ["sector", "size"]}
        self.assertEqual(cell_mismatch(card), [])

        # The country layer is added when consuming the record against a cell whose
        # country the record does not name — that one genuinely moves with the target.
        card = {"population": {"status": "bridged", "bridged_on": ["country", "sector"]},
                "not_measured_on": ["sector"]}
        self.assertEqual(cell_mismatch(card), ["country"])

    def test_fit_never_renders_without_naming_its_target(self):
        from engine.provenance import format_fit

        cell = {"country": "GB", "industry": "finance",
                "company_size": "mid_market", "threat": "data_breach"}
        bridged = format_fit(
            {"population": {"status": "bridged", "bridged_on": ["country"]},
             "not_measured_on": []}, cell)
        self.assertIn("GB · finance · mid_market · data_breach", bridged)
        matched = format_fit(
            {"population": {"status": "matched", "bridged_on": []},
             "not_measured_on": []}, cell)
        self.assertIn("GB · finance · mid_market · data_breach", matched)

    def test_declared_for_is_not_labelled_as_the_observed_population(self):
        # Measured 2026-08-14: 17 of 141 records declare a narrow value on a facet
        # their own `population_match` says the source did not measure, so
        # `applicability` is the cell a record is authored for and not the
        # population observed. ADR-0011 asserted otherwise; publishing this field
        # as "measured on" would swap one mislabel for another.
        markdown = format_portfolio_markdown(build_portfolio_provenance(ROOT))
        self.assertIn("| Declared for |", markdown)
        self.assertNotIn("| Measured on |", markdown)

        out = format_provenance(self.prov, parameter="frequency.min")
        self.assertIn("Declared for :", out)
        self.assertIn("Not measured on :", out)
        self.assertNotIn("Measured on :", out)

    def test_the_contradiction_is_still_measurable_and_still_reported(self):
        # If a future evidence pass reconciles every record, this count goes to zero
        # and the published correction must be revisited rather than left standing.
        import yaml

        facets = {"sector": "industries", "size": "company_size_bands",
                  "country": "countries", "threat": "threats"}
        contradicting = 0
        for path in sorted((ROOT / "evidence").glob("*.yaml")):
            records = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("records", [])
            for record in records:
                declared = record.get("applicability") or {}
                bridged_on = (record.get("population_match") or {}).get("bridged_on") or []
                narrow = [
                    dim for dim in bridged_on
                    if (declared.get(facets[dim]) or [])
                    and not {"all", "global"} & set(declared.get(facets[dim]) or [])
                ]
                contradicting += 1 if narrow else 0
        self.assertGreater(
            contradicting, 0,
            "no record now contradicts its own population_match — the published "
            "'declared for is not the observed population' correction needs revisiting",
        )

    def test_no_composite_fit_score_is_published(self):
        # ADR-0011 part 2, pinned to the surface rather than to intent: a scalar
        # re-imports the portability claim ADR-0010 retired.
        for card in self.prov["cards"]:
            self.assertNotIn("fit_score", card)
            self.assertNotIn("fit_grade", card)
        markdown = format_portfolio_markdown(build_portfolio_provenance(ROOT))
        flat = markdown.replace("\n", " ").lower()
        self.assertIn("summarised into a score, grade or percentage", flat)


if __name__ == "__main__":
    unittest.main()
