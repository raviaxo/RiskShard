import unittest
import tempfile
from pathlib import Path

from engine.currency import convert_currency, load_fx_rates


class CurrencyTests(unittest.TestCase):
    def test_usd_to_aud_conversion_uses_sourced_inverse_rate(self):
        fx_rates = load_fx_rates()

        conversion = convert_currency(2580000, "USD", "AUD", fx_rates)

        self.assertEqual(conversion["rate_id"], "inverse:aud_to_usd_rba_f11_1_2026_06_01")
        self.assertEqual(conversion["inverted_from_rate_id"], "aud_to_usd_rba_f11_1_2026_06_01")
        self.assertAlmostEqual(conversion["rate"], 1.391207568169171)
        self.assertAlmostEqual(conversion["value"], 2580000 / 0.7188)
        self.assertEqual(conversion["evidence_type"], "source_backed")
        self.assertEqual(conversion["retrieved_at"], "2026-06-01")
        self.assertIn("F11.1 Exchange Rates", conversion["citation_detail"])

    def test_identity_conversion_does_not_need_rate_entry(self):
        fx_rates = load_fx_rates()

        conversion = convert_currency(100000, "AUD", "AUD", fx_rates)

        self.assertEqual(conversion["value"], 100000)
        self.assertEqual(conversion["rate"], 1.0)

    def test_estimated_conversion_remains_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fx.yaml"
            path.write_text(
                "rates:\n"
                "  - id: usd_to_aud_estimated\n"
                "    from: USD\n"
                "    to: AUD\n"
                "    rate: 1.5\n"
                "    as_of: '2026-05-26'\n"
                "    source_name: RiskShard planning assumption\n"
                "    source_type: model_assumption\n"
                "    evidence_type: estimated\n"
                "    notes: Planning fallback only.\n"
            )

            conversion = convert_currency(100, "USD", "AUD", load_fx_rates(path))

        self.assertEqual(conversion["rate_id"], "usd_to_aud_estimated")
        self.assertEqual(conversion["value"], 150)
        self.assertEqual(conversion["evidence_type"], "estimated")


if __name__ == "__main__":
    unittest.main()
