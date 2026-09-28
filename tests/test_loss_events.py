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

    def test_external_contributions_is_a_count_not_none(self):
        """It returned None until ADR-0022 gave every record a `contribution` block.

        None was the honest value while nothing recorded who supplied an entry, and the
        roadmap published the owner's assertion beside it. Now it is counted, so a
        regression to None would quietly turn a measured zero back into an asserted one
        — which is the whole distinction ADR-0022 exists to hold.
        """
        metrics = trial_metrics(ROOT)
        self.assertIsInstance(metrics["external_contributions"], int)
        self.assertEqual(
            metrics["external_contributions"], len(metrics["external_contribution_ids"]),
            "the count and the ids behind it disagree")

    def test_every_record_declares_where_it_came_from(self):
        """Required, not optional: absent and zero have to stay distinguishable."""
        for event in load_loss_events(ROOT):
            origin = (event.get("contribution") or {}).get("origin")
            self.assertIn(origin, {"project", "external"}, event["id"])

    def test_the_meter_moves_when_an_external_record_arrives(self):
        """`trial_metrics` itself has to count it, against a registry on disk.

        Without this, `external_contributions` could be hard-wired to 0 and every other
        assertion in this file would still pass — the registry holds no external record
        today, so a meter that always reads zero is indistinguishable from a working one.
        An outside contribution arrives as its own file (ADR-0022), which is the shape
        built here.
        """
        import yaml

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "loss_events").mkdir()
        source = next((ROOT / "loss_events").glob("*.yaml"))
        payload = yaml.safe_load(source.read_text(encoding="utf-8"))
        shutil.copy(source, tmp / "loss_events" / source.name)

        donated = dict(payload["events"][0])
        donated["id"] = "contributed_example_event"
        donated["contribution"] = {
            "origin": "external",
            "contributor": "a-handle",
            "contributed_date": "2026-10-15",
        }
        (tmp / "loss_events" / "contributed.yaml").write_text(
            yaml.safe_dump({"events": [donated]}, sort_keys=False), encoding="utf-8")

        metrics = trial_metrics(tmp)
        self.assertEqual(1, metrics["external_contributions"])
        self.assertEqual(["contributed_example_event"],
                         metrics["external_contribution_ids"])

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

    def test_a_record_with_no_contribution_block_is_rejected(self):
        """ADR-0022 made it required so that absent cannot be read as zero."""
        root = self._registry_copy(lambda event: event.pop("contribution", None))
        errors = validate_loss_events(root)
        self.assertTrue(any("schema" in e for e in errors),
                        f"a record with no `contribution` passed validation: {errors}")

    def test_an_unknown_contribution_origin_is_rejected(self):
        def mutate(event):
            event["contribution"] = {"origin": "somewhere_else"}
        errors = validate_loss_events(self._registry_copy(mutate))
        self.assertTrue(any("schema" in e for e in errors),
                        f"an unknown origin passed validation: {errors}")

    def test_an_external_contribution_must_name_who_and_when(self):
        """Attributable rather than self-asserted, and dated against 2026-11-01.

        A contribution that arrives after the measurement date does not count toward it,
        so a record that cannot say when it arrived cannot be counted either way.
        """
        for missing in ("contributor", "contributed_date"):
            with self.subTest(missing=missing):
                def mutate(event, missing=missing):
                    block = {
                        "origin": "external",
                        "contributor": "a-handle",
                        "contributed_date": "2026-10-15",
                    }
                    block.pop(missing)
                    event["contribution"] = block
                errors = validate_loss_events(self._registry_copy(mutate))
                self.assertTrue(
                    any("schema" in e for e in errors),
                    f"an external record with no {missing} passed validation: {errors}")

    def test_a_complete_external_contribution_is_accepted(self):
        """The guard must reject what is wrong without blocking the thing it measures."""
        def mutate(event):
            event["contribution"] = {
                "origin": "external",
                "contributor": "a-handle",
                "contributed_date": "2026-10-15",
            }
        self.assertEqual([], validate_loss_events(self._registry_copy(mutate)))

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
    """Both of ADR-0017's metrics are generated, so the roadmap must state what they say.

    Added 2026-09-27, when M4 published both metrics as "0 today" — undated, and neither
    pinned. Metric 1 was derivable and was pinned then. Metric 2 was not derivable at all
    (a loss event recorded no supplier, so `trial_metrics` returned None rather than 0),
    so it carried a measurement date and an open decision instead of a pin.

    [ADR-0022](../docs/adr/0022-the-second-kill-metric-gets-a-meter.md) closed that on
    2026-09-28 and metric 2 is pinned here too. The number it publishes did not change;
    what changed is that something generates it, and that is exactly the kind of claim
    that goes stale silently — the roadmap said "0" for weeks with nothing behind it.
    """

    def test_the_roadmap_states_the_live_value_of_metric_one(self):
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        citing = trial_metrics(ROOT)["shards_citing_a_registry_entry"]
        shards = len(citation_candidates(ROOT))
        figure = f"**{citing} of {shards}**"
        self.assertIn(
            figure, roadmap,
            f"docs/ROADMAP.md M4 no longer states metric 1 as {figure}")

    def test_the_roadmap_states_the_live_value_of_metric_two(self):
        metrics = trial_metrics(ROOT)
        figure = f"**{metrics['external_contributions']} of {metrics['registry_events']}**"
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn(
            figure, roadmap,
            f"docs/ROADMAP.md M4 no longer states metric 2 as {figure}")

    def test_the_roadmap_no_longer_calls_metric_two_underivable(self):
        """The sentence ADR-0022 made false must not survive it.

        It read "this one cannot be derived from the tree". It can now, and a claim that
        the project cannot measure its own kill criterion is the last one that should be
        left lying around 34 days before the measurement.
        """
        roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        self.assertNotIn("cannot\n   be derived from the tree", roadmap)
        self.assertNotIn("returns `None`", roadmap)
