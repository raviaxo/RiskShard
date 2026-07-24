import unittest

from engine.interop import PYFAIR_LEF, PYFAIR_LM, format_pyfair_code, to_pyfair

SCENARIO = {
    "metadata": {"name": "Japan Manufacturing Ransomware Midmarket", "currency": "USD"},
    "frequency": {"min": 0.10, "likely": 0.25, "max": 0.50},
    "impact": {"min": 6000, "likely": 1300000, "max": 5000000},
}


class ToPyfairTests(unittest.TestCase):
    def test_pert_maps_to_betapert_low_mode_high(self):
        mapped = to_pyfair(SCENARIO)
        self.assertEqual(mapped[PYFAIR_LEF], {"low": 0.10, "mode": 0.25, "high": 0.50})
        self.assertEqual(mapped[PYFAIR_LM], {"low": 6000, "mode": 1300000, "high": 5000000})
        self.assertEqual(mapped["currency"], "USD")

    def test_missing_triangle_raises(self):
        with self.assertRaises(ValueError):
            to_pyfair({"metadata": {}, "frequency": {"min": 0.1}, "impact": {}})

    def test_out_of_order_triangle_raises(self):
        bad = {"metadata": {}, "frequency": {"min": 0.5, "likely": 0.2, "max": 0.1}, "impact": SCENARIO["impact"]}
        with self.assertRaises(ValueError):
            to_pyfair(bad)


class FormatPyfairTests(unittest.TestCase):
    def test_code_is_runnable_pyfair_and_keeps_provenance_pointer(self):
        code = format_pyfair_code(SCENARIO, module_id="jp_manufacturing_ransomware_midmarket")
        self.assertIn("from pyfair import FairModel", code)
        self.assertIn("model.input_data('Loss Event Frequency', low=0.1, mode=0.25, high=0.5)", code)
        # the evidence trail survives the hand-off
        self.assertIn("provenance jp_manufacturing_ransomware_midmarket", code)


if __name__ == "__main__":
    unittest.main()
