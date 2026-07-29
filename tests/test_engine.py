import json
import random
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from jsonschema.exceptions import ValidationError

from engine import fair_calc


ROOT = Path(__file__).resolve().parents[1]


class SchemaValidationTests(unittest.TestCase):
    def test_sample_scenario_validates_against_schema(self):
        schema = fair_calc.load_schema()
        config = fair_calc.load_and_validate(ROOT / "scenarios" / "ransomware.yaml", schema)

        self.assertEqual(config["metadata"]["name"], "Ransomware Attack")
        self.assertEqual(set(config["frequency"]), {"min", "likely", "max"})
        self.assertEqual(set(config["impact"]), {"min", "likely", "max"})

    def test_invalid_scenario_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.yaml"
            path.write_text(
                "metadata:\n"
                "  name: Missing Impact\n"
                "frequency:\n"
                "  min: 0.1\n"
                "  likely: 0.2\n"
                "  max: 0.3\n"
            )

            with self.assertRaises(ValidationError):
                fair_calc.load_and_validate(path, fair_calc.load_schema())


class SimulationTests(unittest.TestCase):
    def test_constant_ranges_produce_constant_losses(self):
        scenario = {
            "metadata": {"name": "Constant Scenario"},
            "frequency": {"min": 2, "likely": 2, "max": 2},
            "impact": {"min": 5, "likely": 5, "max": 5},
        }

        name, results = fair_calc.run_simulation(
            scenario,
            trials=5,
            dist_type="pert",
            rng=random.Random(7),
        )

        self.assertEqual(name, "Constant Scenario")
        self.assertEqual(results, [10, 10, 10, 10, 10])
        self.assertEqual(fair_calc.compute_stats(results)["mean"], 10)

    def test_loss_stage_conditionally_adds_impact(self):
        base = {
            "metadata": {"name": "Chain Scenario"},
            "frequency": {"min": 2, "likely": 2, "max": 2},
            "impact": {"min": 5, "likely": 5, "max": 5},
        }
        always = dict(base, loss_stages=[{
            "loss_mode": "regulatory_penalty",
            "conditional_probability": {"min": 1, "likely": 1, "max": 1},
            "impact": {"min": 3, "likely": 3, "max": 3},
        }])
        never = dict(base, loss_stages=[{
            "loss_mode": "regulatory_penalty",
            "conditional_probability": {"min": 0, "likely": 0, "max": 0},
            "impact": {"min": 3, "likely": 3, "max": 3},
        }])

        _, always_results = fair_calc.run_simulation(
            always, trials=5, dist_type="pert", rng=random.Random(7)
        )
        _, never_results = fair_calc.run_simulation(
            never, trials=5, dist_type="pert", rng=random.Random(7)
        )

        # A stage that always fires adds its impact: 2 * (5 + 3) = 16.
        self.assertEqual(always_results, [16, 16, 16, 16, 16])
        # A stage that never fires leaves the base loss: 2 * 5 = 10.
        self.assertEqual(never_results, [10, 10, 10, 10, 10])

    def test_absent_loss_stages_match_single_event_model(self):
        scenario = {
            "metadata": {"name": "No Stages"},
            "frequency": {"min": 2, "likely": 2, "max": 2},
            "impact": {"min": 5, "likely": 5, "max": 5},
        }
        _, without_key = fair_calc.run_simulation(
            scenario, trials=5, dist_type="pert", rng=random.Random(7)
        )
        _, empty_list = fair_calc.run_simulation(
            dict(scenario, loss_stages=[]), trials=5, dist_type="pert", rng=random.Random(7)
        )
        # No loss_stages (absent or empty) is identical to the single-event model.
        self.assertEqual(without_key, [10, 10, 10, 10, 10])
        self.assertEqual(empty_list, [10, 10, 10, 10, 10])

    def test_triangular_sampling_stays_within_loss_bounds(self):
        scenario = {
            "metadata": {"name": "Bounded Scenario"},
            "frequency": {"min": 1, "likely": 2, "max": 3},
            "impact": {"min": 10, "likely": 20, "max": 30},
        }

        _, results = fair_calc.run_simulation(
            scenario,
            trials=25,
            dist_type="triangular",
            rng=random.Random(11),
        )

        self.assertEqual(len(results), 25)
        self.assertTrue(all(10 <= result <= 90 for result in results))


class PortfolioTests(unittest.TestCase):
    def test_aggregate_portfolio_sums_trial_positions(self):
        aggregate = fair_calc.aggregate_portfolio({
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        })

        self.assertEqual(aggregate, [11, 22, 33])

    def test_compute_all_stats_returns_shards_portfolio_and_aggregate(self):
        shard_stats, portfolio_stats, aggregate = fair_calc.compute_all_stats({
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        })

        self.assertEqual(aggregate, [11, 22, 33])
        self.assertIn("a", shard_stats)
        self.assertEqual(portfolio_stats["mean"], 22)

    def test_run_portfolio_records_isolated_seed_metadata(self):
        first = fair_calc.run_portfolio(
            ROOT / "scenarios",
            trials=10,
            dist_type="pert",
            seed=123,
        )
        second = fair_calc.run_portfolio(
            ROOT / "scenarios",
            trials=10,
            dist_type="pert",
            seed=123,
        )

        self.assertEqual(first["aggregate"], second["aggregate"])
        self.assertEqual(first["portfolio"], second["portfolio"])

        reproducibility = first["metadata"]["reproducibility"]
        self.assertTrue(reproducibility["deterministic"])
        self.assertEqual(reproducibility["base_seed"], 123)
        self.assertEqual(reproducibility["seed_source"], "cli")
        self.assertEqual(reproducibility["rng_isolation"], "per_scenario")
        self.assertEqual(first["metadata"]["input_path"], str(ROOT / "scenarios"))
        self.assertIn("--seed 123", reproducibility["reproduction_command"])
        self.assertIn("--trials 10", reproducibility["reproduction_command"])

        scenario_metadata = reproducibility["scenarios"]
        seeds = [scenario["seed"] for scenario in scenario_metadata]
        self.assertEqual(len(scenario_metadata), len(fair_calc.scenario_files(ROOT / "scenarios")))
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertTrue(all(0 <= seed <= 0xFFFFFFFF for seed in seeds))
        self.assertTrue(all(scenario["fingerprint"] for scenario in scenario_metadata))
        self.assertIn("currency", scenario_metadata[0])
        self.assertIn("GBP", first["metadata"]["currencies"]["unique"])
        self.assertTrue(first["metadata"]["currencies"]["mixed_or_unspecified"])
        self.assertIsNone(first["metadata"]["currencies"]["portfolio_currency"])
        self.assertIn("unconverted", first["metadata"]["currencies"]["warning"])

    def test_scenario_seed_is_stable_when_portfolio_order_changes(self):
        scenario = {
            "metadata": {"name": "Stable Seed"},
            "frequency": {"min": 1, "likely": 1, "max": 1},
            "impact": {"min": 1, "likely": 1, "max": 1},
        }

        first = fair_calc.derive_scenario_seed(42, Path("scenarios/stable.yaml"), scenario)
        second = fair_calc.derive_scenario_seed(42, Path("scenarios/stable.yaml"), scenario)
        renamed = fair_calc.derive_scenario_seed(42, Path("scenarios/renamed.yaml"), scenario)

        self.assertEqual(first, second)
        self.assertNotEqual(first, renamed)

    def test_scenario_seed_does_not_depend_on_where_the_repo_lives(self):
        """ADR-0002: a published number must be reproducible on another machine.

        The seed used to mix in the scenario's absolute path, so the same shard gave
        different numbers under /Users/... than under /home/runner/... . The earlier
        test only ever passed relative paths, which is why it never caught this.
        """
        scenario = {
            "metadata": {"name": "Portable Seed"},
            "frequency": {"min": 1, "likely": 1, "max": 1},
            "impact": {"min": 1, "likely": 1, "max": 1},
        }

        here = fair_calc.derive_scenario_seed(
            42, Path("/Users/someone/RiskShard/scenarios/x.yaml"), scenario,
            root=Path("/Users/someone/RiskShard"))
        on_ci = fair_calc.derive_scenario_seed(
            42, Path("/home/runner/work/RiskShard/RiskShard/scenarios/x.yaml"), scenario,
            root=Path("/home/runner/work/RiskShard/RiskShard"))

        self.assertEqual(here, on_ci)

    def test_out_of_tree_scenario_seed_ignores_its_directory(self):
        """A scenario outside the project root keys on its filename, not its path."""
        self.assertEqual(
            fair_calc.portable_scenario_key("/tmp/alice/custom.yaml"),
            fair_calc.portable_scenario_key("/var/bob/deeper/custom.yaml"),
        )

    def test_simulation_output_is_pinned(self):
        """Golden value: the numbers themselves must not drift silently.

        Nothing in the suite asserted simulated output, so the seed defect above
        passed CI unnoticed. Verified identical on Python 3.8 and 3.14, so this pins
        across interpreter versions as well as machines.
        """
        config = {
            "metadata": {"name": "Golden"},
            "frequency": {"min": 0.1, "likely": 0.3, "max": 0.6},
            "impact": {"min": 1000, "likely": 5000, "max": 20000},
        }
        seed = fair_calc.derive_scenario_seed(42, "scenarios/golden.yaml", config)
        self.assertEqual(seed, 4159219580)

        _, losses = fair_calc.run_simulation(config, 2000, "pert", random.Random(seed))
        self.assertEqual(len(losses), 2000)
        self.assertAlmostEqual(sum(losses) / len(losses), 2132.6034904873, places=6)
        self.assertAlmostEqual(
            fair_calc.percentile(sorted(losses), 0.95), 4508.3801874242, places=6)

    def test_export_report_includes_optional_metadata(self):
        metadata = {
            "trials": 25,
            "distribution": "pert",
            "reproducibility": {
                "deterministic": True,
                "base_seed": 7,
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            path = fair_calc.export_report(
                {"example": {"mean": 1}},
                {"mean": 1},
                output_dir=tmp,
                timestamp=datetime(2026, 1, 2, 3, 4, 5),
                metadata=metadata,
            )

            payload = json.loads(Path(path).read_text())

        self.assertEqual(payload["timestamp"], "2026-01-02T03:04:05")
        self.assertEqual(payload["metadata"], metadata)

    def test_export_report_carries_impact_uncertainty_caveat(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = fair_calc.export_report(
                {"example": {"mean": 1}},
                {"mean": 1},
                output_dir=tmp,
                timestamp=datetime(2026, 1, 2, 3, 4, 5),
            )
            payload = json.loads(Path(path).read_text())

        self.assertIn(fair_calc.IMPACT_UNCERTAINTY_NOTE, payload["caveats"])

    def test_export_report_flags_loss_chain_when_present(self):
        metadata_with_stages = {
            "reproducibility": {
                "scenarios": [
                    {"name": "Chain", "loss_stages": [{"loss_mode": "regulatory_penalty"}]}
                ]
            }
        }
        metadata_without = {
            "reproducibility": {"scenarios": [{"name": "Plain", "loss_stages": []}]}
        }
        with tempfile.TemporaryDirectory() as tmp:
            with_path = fair_calc.export_report(
                {"Chain": {"mean": 1}}, {"mean": 1}, output_dir=tmp,
                timestamp=datetime(2026, 1, 2, 3, 4, 5), metadata=metadata_with_stages,
            )
            without_path = fair_calc.export_report(
                {"Plain": {"mean": 1}}, {"mean": 1}, output_dir=tmp,
                timestamp=datetime(2026, 1, 2, 3, 4, 6), metadata=metadata_without,
            )
            with_payload = json.loads(Path(with_path).read_text())
            without_payload = json.loads(Path(without_path).read_text())

        self.assertIn(fair_calc.LOSS_CHAIN_NOTE, with_payload["caveats"])
        self.assertNotIn(fair_calc.LOSS_CHAIN_NOTE, without_payload["caveats"])

    def test_run_portfolio_records_loss_stages_in_scenario_metadata(self):
        result = fair_calc.run_portfolio(
            "scenarios/gb_finance_data_breach_regulatory_chain.yaml",
            trials=200, dist_type="pert", seed=42,
        )
        scenario = result["metadata"]["reproducibility"]["scenarios"][0]
        self.assertTrue(scenario["loss_stages"])
        self.assertEqual(scenario["loss_stages"][0]["loss_mode"], "regulatory_penalty")

    def test_executive_report_includes_impact_uncertainty_caveat(self):
        from engine.executive_report import build_executive_report

        run = {
            "portfolio": {"mean": 1, "p50": 1, "p95": 2, "p99": 3},
            "metadata": {"trials": 10, "distribution": "pert"},
        }
        report = build_executive_report(run, module={}, pack={})

        self.assertIn(fair_calc.IMPACT_UNCERTAINTY_NOTE, report["caveats"])


if __name__ == "__main__":
    unittest.main()
