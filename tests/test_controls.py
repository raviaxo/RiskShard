import unittest

from engine.controls.engine import apply_controls
from engine.controls.library import FrequencyReduction, ImpactReduction


class ControlTransformationTests(unittest.TestCase):
    def test_frequency_reduction_scales_existing_range_fields(self):
        scenario = {
            "frequency": {"min": 0.1, "likely": 0.2, "max": 0.4},
            "impact": {"min": 100, "likely": 200, "max": 400},
        }

        updated = FrequencyReduction(0.25).apply(scenario)

        self.assertAlmostEqual(updated["frequency"]["min"], 0.075)
        self.assertAlmostEqual(updated["frequency"]["likely"], 0.15)
        self.assertAlmostEqual(updated["frequency"]["max"], 0.3)
        self.assertEqual(scenario["frequency"]["likely"], 0.2)

    def test_impact_reduction_scales_existing_range_fields(self):
        scenario = {
            "frequency": {"min": 0.1, "likely": 0.2, "max": 0.4},
            "impact": {"min": 100, "likely": 200, "max": 400},
        }

        updated = ImpactReduction(0.5).apply(scenario)

        self.assertEqual(updated["impact"], {
            "min": 50,
            "likely": 100,
            "max": 200,
        })
        self.assertEqual(scenario["impact"]["likely"], 200)

    def test_apply_controls_chains_transformations(self):
        scenario = {
            "frequency": {"min": 0.1, "likely": 0.2, "max": 0.4},
            "impact": {"min": 100, "likely": 200, "max": 400},
        }

        updated = apply_controls(
            scenario,
            [FrequencyReduction(0.5), ImpactReduction(0.25)],
        )

        self.assertAlmostEqual(updated["frequency"]["min"], 0.05)
        self.assertAlmostEqual(updated["frequency"]["likely"], 0.1)
        self.assertAlmostEqual(updated["frequency"]["max"], 0.2)
        self.assertEqual(updated["impact"], {
            "min": 75.0,
            "likely": 150.0,
            "max": 300.0,
        })


if __name__ == "__main__":
    unittest.main()
