import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from engine import backtesting


def rec(country, naics, year, breach=True):
    record = {
        "victim": {"country": [country], "industry": naics},
        "timeline": {"incident": {"year": year}},
        "attribute": {},
    }
    if breach:
        record["attribute"]["confidentiality"] = {"data": []}
    return record


SAMPLE = [
    rec("GB", "521000", 2015),
    rec("GB", "522110", 2017),
    rec("GB", "999999", 2016),            # not finance
    rec("GB", "521000", 2018, breach=False),  # not a breach
    rec("US", "523000", 2019),
    rec("US", "521000", 2010),            # before since_year
]


class FilterTests(unittest.TestCase):
    def test_filter_cell_matches_country_industry_breach_and_year(self):
        gb = backtesting.filter_cell(SAMPLE, "GB", since_year=2015)
        years = sorted(backtesting.incident_year(r) for r in gb)
        self.assertEqual(years, [2015, 2017])  # excludes non-finance, non-breach

    def test_filter_cell_respects_since_year(self):
        us = backtesting.filter_cell(SAMPLE, "US", since_year=2015)
        self.assertEqual(len(us), 1)  # 2010 excluded

    def test_annual_counts_zero_fills_the_span(self):
        gb = backtesting.filter_cell(SAMPLE, "GB", since_year=2015)
        counts = backtesting.annual_counts(gb, since_year=2015)
        self.assertEqual(counts, {2015: 1, 2016: 0, 2017: 1})


class DispersionTests(unittest.TestCase):
    def test_flat_counts_are_poisson_consistent(self):
        stats = backtesting.dispersion_stats({2015: 5, 2016: 5, 2017: 5})
        self.assertEqual(stats["verdict"], "poisson_consistent")

    def test_spiky_counts_are_overdispersed(self):
        stats = backtesting.dispersion_stats({2015: 0, 2016: 1, 2017: 60})
        self.assertGreater(stats["dispersion_index"], 3.0)
        self.assertEqual(stats["verdict"], "strong_overdispersion")

    def test_empty_counts_are_safe(self):
        stats = backtesting.dispersion_stats({})
        self.assertEqual(stats["verdict"], "no_data")


class FitTests(unittest.TestCase):
    def test_negbin_mom_none_when_not_overdispersed(self):
        self.assertIsNone(backtesting.negbin_mom({2015: 5, 2016: 5, 2017: 5}))

    def test_negbin_mom_fits_when_overdispersed(self):
        nb = backtesting.negbin_mom({2015: 0, 2016: 1, 2017: 60})
        self.assertIsNotNone(nb)
        self.assertGreater(nb["r"], 0)
        self.assertTrue(0 < nb["p"] < 1)

    def test_fit_comparison_prefers_negbin_under_overdispersion(self):
        fit = backtesting.fit_comparison({2015: 0, 2016: 1, 2017: 60})
        self.assertTrue(fit["overdispersed"])
        self.assertEqual(fit["better_fit"], "negbin")
        self.assertGreater(fit["loglik_gain"], 0)

    def test_fit_comparison_prefers_poisson_when_flat(self):
        fit = backtesting.fit_comparison({2015: 5, 2016: 5, 2017: 5})
        self.assertFalse(fit["overdispersed"])
        self.assertEqual(fit["better_fit"], "poisson")

    def test_fit_comparison_needs_two_years(self):
        self.assertFalse(backtesting.fit_comparison({2015: 3})["comparable"])


class BracketTests(unittest.TestCase):
    def test_rate_inside_band_is_within_band_and_om(self):
        band = {"min": 0.4, "likely": 0.6, "max": 0.7}
        result = backtesting.order_of_magnitude_bracket(band, 0.5)
        self.assertTrue(result["within_band"])
        self.assertTrue(result["within_order_of_magnitude"])

    def test_rate_far_below_band_fails_order_of_magnitude(self):
        band = {"min": 0.4, "likely": 0.6, "max": 0.7}
        result = backtesting.order_of_magnitude_bracket(band, 0.001)
        self.assertFalse(result["within_band"])
        self.assertFalse(result["within_order_of_magnitude"])


class ReportTests(unittest.TestCase):
    def test_report_has_frequency_only_scope_and_implied_firms(self):
        provenance = {"dataset": "VCDB", "license": "CC BY-SA 4.0",
                      "sha256": "deadbeef" * 8, "record_count": len(SAMPLE)}
        band = {"min": 0.4, "likely": 0.5, "max": 0.7}
        report = backtesting.build_frequency_backtest_report(
            SAMPLE, provenance, shard_id="gb_test", shard_frequency=band,
            primary_country="GB", secondary_country="US", since_year=2015,
        )
        self.assertEqual(report["scope"], "frequency_only")
        self.assertEqual(report["primary_cell"]["country"], "GB")
        # mean GB count over 2015-2017 = 2 incidents / 3 years
        self.assertAlmostEqual(report["primary_cell"]["dispersion"]["mean"], 2 / 3)
        self.assertIsNotNone(report["implied_covered_firms"])
        text = backtesting.format_frequency_backtest_report(report)
        self.assertIn("FREQUENCY ONLY", text)


class LoaderTests(unittest.TestCase):
    def test_load_reads_zipped_json_and_reports_provenance(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("vcdb.json", json.dumps(SAMPLE))
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "vcdb.json.zip"
            cache.write_bytes(buffer.getvalue())
            records, provenance = backtesting.load_vcdb_records(
                cache_path=cache, allow_download=False)
        self.assertEqual(len(records), len(SAMPLE))
        self.assertEqual(provenance["record_count"], len(SAMPLE))
        self.assertEqual(len(provenance["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
