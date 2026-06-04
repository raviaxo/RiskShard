import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class FxRateRefreshTests(unittest.TestCase):
    def test_update_fx_rates_writes_sourced_rba_rate_from_fixture(self):
        csv_text = (
            "Title,A$1=USD,Trade-weighted Index May 1970 = 100\n"
            "Description,AUD/USD Exchange Rate; see notes for further detail.,Australian Dollar Trade-weighted Index\n"
            "Frequency,Daily,Daily\n"
            "Type,Indicative,Indicative\n"
            "Units,USD,Index\n"
            "\n"
            "Source,WM/Reuters,RBA\n"
            "Publication date,01-Jun-2026,01-Jun-2026\n"
            "Series ID,FXRUSD,FXRTWI\n"
            "29-May-2026,0.7164,66.60\n"
            "01-Jun-2026,0.7188,66.80\n"
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            input_csv = Path(tmp) / "f11.1-data.csv"
            output_yaml = Path(tmp) / "fx_rates.yaml"
            input_csv.write_text(csv_text)

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/update_fx_rates.py",
                    "--input-csv",
                    str(input_csv),
                    "--output",
                    str(output_yaml),
                    "--retrieved-at",
                    "2026-06-01",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )
            payload = yaml.safe_load(output_yaml.read_text())

        rate = payload["rates"][0]
        self.assertEqual(rate["id"], "aud_to_usd_rba_f11_1_2026_06_01")
        self.assertEqual(rate["rate"], 0.7188)
        self.assertEqual(rate["as_of"], "2026-06-01")
        self.assertEqual(rate["retrieved_at"], "2026-06-01")
        self.assertEqual(rate["evidence_type"], "source_backed")
        self.assertIn("F11.1 Exchange Rates", rate["citation_detail"])

    def test_update_fx_rates_preserves_other_configured_rates(self):
        csv_text = (
            "Title,A$1=USD,Trade-weighted Index May 1970 = 100\n"
            "Description,AUD/USD Exchange Rate; see notes for further detail.,Australian Dollar Trade-weighted Index\n"
            "Frequency,Daily,Daily\n"
            "Type,Indicative,Indicative\n"
            "Units,USD,Index\n"
            "\n"
            "Source,WM/Reuters,RBA\n"
            "Publication date,01-Jun-2026,01-Jun-2026\n"
            "Series ID,FXRUSD,FXRTWI\n"
            "01-Jun-2026,0.7188,66.80\n"
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        with tempfile.TemporaryDirectory() as tmp:
            input_csv = Path(tmp) / "f11.1-data.csv"
            output_yaml = Path(tmp) / "fx_rates.yaml"
            input_csv.write_text(csv_text)
            output_yaml.write_text(
                "rates:\n"
                "  - id: gbp_to_usd_ecb_cross_2026_06_04\n"
                "    from: GBP\n"
                "    to: USD\n"
                "    rate: 1.345820326049254\n"
                "    as_of: '2026-06-04'\n"
                "    source_name: European Central Bank euro foreign exchange reference rates\n"
                "    source_type: official_reference_rate\n"
                "    source_url: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html\n"
                "    retrieved_at: '2026-06-04'\n"
                "    citation_detail: ECB cross-rate fixture.\n"
                "    evidence_type: source_backed\n"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/update_fx_rates.py",
                    "--input-csv",
                    str(input_csv),
                    "--output",
                    str(output_yaml),
                    "--retrieved-at",
                    "2026-06-01",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = yaml.safe_load(output_yaml.read_text())

        self.assertEqual(
            [rate["id"] for rate in payload["rates"]],
            [
                "aud_to_usd_rba_f11_1_2026_06_01",
                "gbp_to_usd_ecb_cross_2026_06_04",
            ],
        )


if __name__ == "__main__":
    unittest.main()
