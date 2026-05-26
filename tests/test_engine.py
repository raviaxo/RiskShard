import random
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
