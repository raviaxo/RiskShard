"""The loss-event registry (ADR-0012), and the rules that keep it from becoming a dataset.

The registry is the one place in this repo where a record names an identifiable company
and a figure it disclosed. The bar is therefore higher than elsewhere: every amount
typed, every figure quoted, every record saying what it cannot support — and no path by
which a consumer can accidentally average across amount types that mean different things.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.loss_events import (
    GROSS_EVENT_TYPES,
    NON_LOSS_TYPES,
    citation_candidates,
    gross_event_amounts,
    load_loss_events,
    registry_summary,
    trial_metrics,
    validate_loss_events,
)

ROOT = Path(__file__).resolve().parents[1]


class RegistryIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = load_loss_events(ROOT)

    def test_registry_validates_clean(self):
        self.assertEqual(validate_loss_events(ROOT), [])

    def test_every_amount_is_typed_and_quoted(self):
        for event in self.events:
            for amount in event["amounts"]:
                self.assertIn(amount["type"], GROSS_EVENT_TYPES | NON_LOSS_TYPES, event["id"])
                self.assertTrue(amount["cited_line"].strip(), event["id"])
                self.assertGreater(amount["value"], 0, event["id"])

    def test_every_record_says_what_it_cannot_support(self):
        for event in self.events:
            self.assertIn("never", event["limitations"].lower(), event["id"])

    def test_every_record_is_human_confirmed(self):
        """ADR-0012 forbids automatic extraction; 12 of 50 machine candidates were wrong."""
        for event in self.events:
            self.assertEqual(
                event["verification"]["method"], "machine_candidate_human_confirmed", event["id"]
            )

    def test_small_figures_declare_where_their_units_came_from(self):
        """The census hazard: a statement-table figure read at face value is off by 1000x."""
        for event in self.events:
            for amount in event["amounts"]:
                if amount["value"] < 10_000:
                    self.assertTrue(
                        amount.get("units_resolved_from"),
                        f"{event['id']}: {amount['value']} must say where its units came from",
                    )

    def test_ids_are_unique_and_stable_shaped(self):
        ids = [e["id"] for e in self.events]
        self.assertEqual(len(ids), len(set(ids)))
        for eid in ids:
            self.assertRegex(eid, r"^[a-z0-9_]+$")

    def test_every_source_is_a_resolvable_https_filing_url(self):
        for event in self.events:
            self.assertTrue(event["source"]["url"].startswith("https://"), event["id"])


class TypedAmountTests(unittest.TestCase):
    """The typing is the point: recoveries are not losses."""

    @classmethod
    def setUpClass(cls):
        cls.events = load_loss_events(ROOT)

    def test_gross_amounts_exclude_recoveries_settlements_and_deltas(self):
        for event in self.events:
            for amount in gross_event_amounts(event):
                self.assertNotIn(amount["type"], NON_LOSS_TYPES, event["id"])

    def test_the_registry_actually_contains_non_loss_amounts(self):
        """If it did not, the typing would be untested by the data itself."""
        summary = registry_summary(ROOT)
        self.assertGreater(
            summary["non_loss_amounts"], 0,
            "the corpus is known to mix recoveries and settlements with costs",
        )

    def test_gross_and_non_loss_types_are_disjoint(self):
        self.assertEqual(GROSS_EVENT_TYPES & NON_LOSS_TYPES, frozenset())

    def test_a_recovery_only_record_yields_no_gross_amount(self):
        """Tenet and TTEC disclose an insurance recovery and never the gross loss.

        A consumer asking for event costs must get nothing from them, rather than a
        recovery silently standing in for a loss.
        """
        recovery_only = [e for e in self.events if not gross_event_amounts(e)]
        self.assertTrue(recovery_only, "expected at least one recovery-only record")
        for event in recovery_only:
            self.assertTrue(
                all(a["type"] in NON_LOSS_TYPES for a in event["amounts"]), event["id"]
            )


class BoundedTrialTests(unittest.TestCase):
    """ADR-0012 adopted this with a retirement test. The test has to be computable."""

    def test_trial_metrics_report_the_kill_criterion_inputs(self):
        metrics = trial_metrics(ROOT)
        self.assertIn("shards_citing_a_registry_entry", metrics)
        self.assertIn("external_contributions", metrics)
        self.assertGreater(metrics["registry_events"], 0)

    def test_external_contributions_is_unmeasured_not_zero(self):
        """None means nobody has recorded it. Reporting 0 would assert a fact we lack."""
        self.assertIsNone(trial_metrics(ROOT)["external_contributions"])

    def test_zero_citations_is_explained_not_just_counted(self):
        """"No shard cites an entry" only argues for retirement if some shard could.

        Right now none can, and the reasons are structural rather than neglect: the
        corpus is US/GB/IE while most shards are AU/CA/DE/FR/JP/SG, and it holds no
        business-email-compromise events at all. Recording that distinction is the
        difference between a trial that failed and a trial still running.
        """
        candidates = citation_candidates(ROOT)
        self.assertEqual(len(candidates), 11)
        no_match = [c for c in candidates if not c["candidates"]]
        self.assertGreater(
            len(no_match), 0,
            "expected shards with no country+threat match against a US-listed corpus",
        )

    def test_a_candidate_is_blocked_when_it_would_lose_an_exceedance_statement(self):
        """ADR-0008: a maximum that says how often it is exceeded outranks one that does not.

        us_finance_data_breach_midmarket has genuine country+threat matches, and its
        current maximum carries observed_rank. Swapping it for a registry entry — which
        carries no exceedance by rule — would trade information for provenance.
        """
        blocked = [c for c in citation_candidates(ROOT) if c["blocked_by_exceedance_loss"]]
        self.assertTrue(blocked, "expected at least one match blocked on exceedance grounds")
        for candidate in blocked:
            self.assertTrue(candidate["candidates"])
            self.assertFalse(candidate["citable"])
            self.assertIn(candidate["current_exceedance"], ("observed_rank", "modeled_quantile"))

    def test_no_aggregate_is_exposed(self):
        """ADR-0012 forbids a central tendency over this corpus, so none is computed."""
        summary = registry_summary(ROOT)
        for banned in ("mean", "median", "average", "total_value"):
            self.assertNotIn(banned, summary)


if __name__ == "__main__":
    unittest.main()


class SchemaValidationTests(unittest.TestCase):
    """`schemas/loss_event_schema.json` is applied, and its absence is an error.

    Written 2026-09-27, when this file contained no mention of "schema" at all: the only
    JSON-Schema-validated artifact in the repository had its validation wrapped in a
    silent `except ImportError: pass`, and no test had ever asserted that an invalid
    record is rejected. The schema was, in effect, decorative.
    """

    def _registry_copy(self, mutate):
        """A throwaway root holding the schema and one registry file, mutated."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "schemas").mkdir()
        shutil.copy(ROOT / "schemas" / "loss_event_schema.json", tmp / "schemas")
        (tmp / "loss_events").mkdir()
        import yaml
        source = next((ROOT / "loss_events").glob("*.yaml"))
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        payload["events"] = [dict(payload["events"][0])]
        mutate(payload["events"][0])
        (tmp / "loss_events" / source.name).write_text(
            yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return tmp

    def test_the_live_registry_satisfies_its_own_schema(self):
        self.assertEqual([], validate_loss_events(ROOT))

    def test_a_record_missing_a_required_field_is_rejected(self):
        root = self._registry_copy(lambda event: event.pop("verification", None))
        errors = validate_loss_events(root)
        self.assertTrue(any("schema" in e for e in errors),
                        f"a record with no `verification` passed validation: {errors}")

    def test_a_schema_that_cannot_be_read_is_an_error_not_a_pass(self):
        root = self._registry_copy(lambda event: None)
        (root / "schemas" / "loss_event_schema.json").write_text("{not json",
                                                                encoding="utf-8")
        errors = validate_loss_events(root)
        self.assertTrue(any("could not be read" in e for e in errors),
                        f"an unreadable schema reported clean: {errors}")

    def test_a_missing_jsonschema_is_reported_rather_than_skipped(self):
        """The gate must fail closed. It used to `pass`, reporting clean."""
        import builtins

        root = self._registry_copy(lambda event: None)
        real_import = builtins.__import__

        def refuse_jsonschema(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("simulated missing dependency")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = refuse_jsonschema
        try:
            errors = validate_loss_events(root)
        finally:
            builtins.__import__ = real_import
        self.assertTrue(any("jsonschema is not installed" in e for e in errors),
                        f"a missing jsonschema reported clean: {errors}")


class KillCriterionPublishedFiguresTests(unittest.TestCase):
    """ADR-0017's metric 1 is generated, so the roadmap must state what it generates.

    Added 2026-09-27, when M4 published both of its metrics as "0 today" — undated, and
    neither one pinned. Metric 1 is derivable from the tree and is pinned here. Metric 2
    is not derivable at all (a loss event records no supplier, so `trial_metrics` returns
    None rather than 0) and therefore carries a measurement date in the roadmap instead;
    that gap is recorded in the roadmap as an open decision, not patched over.
    """

    def test_the_roadmap_states_the_live_value_of_metric_one(self):
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        citing = trial_metrics(ROOT)["shards_citing_a_registry_entry"]
        shards = len(citation_candidates(ROOT))
        figure = f"**{citing} of {shards}**"
        self.assertIn(
            figure, roadmap,
            f"docs/ROADMAP.md M4 no longer states metric 1 as {figure}")

    def test_metric_two_is_unmeasured_rather_than_zero(self):
        """If this ever returns a number, the roadmap's wording is owed a revisit.

        `None` is the honest value while nothing records who supplied an entry. A change
        that starts returning 0 or more would make the roadmap's "cannot be derived from
        the tree" false, and that sentence is load-bearing 35 days before the decision.
        """
        self.assertIsNone(trial_metrics(ROOT)["external_contributions"])
