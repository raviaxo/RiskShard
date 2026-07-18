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
