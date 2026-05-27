import unittest

from engine.currency import convert_currency, load_fx_rates


class CurrencyTests(unittest.TestCase):
    def test_usd_to_aud_planning_conversion_is_explicit(self):
        fx_rates = load_fx_rates()

        conversion = convert_currency(2580000, "USD", "AUD", fx_rates)

        self.assertEqual(conversion["rate_id"], "usd_to_aud_planning_2026_05_26")
        self.assertEqual(conversion["value"], 3870000)
        self.assertEqual(conversion["evidence_type"], "estimated")

    def test_identity_conversion_does_not_need_rate_entry(self):
        fx_rates = load_fx_rates()

        conversion = convert_currency(100000, "AUD", "AUD", fx_rates)

        self.assertEqual(conversion["value"], 100000)
        self.assertEqual(conversion["rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
