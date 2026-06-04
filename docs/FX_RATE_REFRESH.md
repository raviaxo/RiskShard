# FX Rate Refresh

RiskShard stores FX assumptions in `calibrations/fx_rates.yaml`. Calibration should read that local file; it should not fetch live FX rates during a risk run.

## Source

The current USD-to-AUD calibration path uses the Reserve Bank of Australia Statistical Table F11.1. RBA quotes `A$1=USD`, so RiskShard stores the AUD-to-USD source rate and explicitly inverts it when a calibration needs USD-to-AUD.

Source CSV:

```text
https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv
```

## Refresh Command

```bash
python scripts/update_fx_rates.py \
  --output calibrations/fx_rates.yaml
```

For a pinned local CSV fixture:

```bash
python scripts/update_fx_rates.py \
  --input-csv path/to/f11.1-data.csv \
  --output calibrations/fx_rates.yaml \
  --retrieved-at 2026-06-01
```

## Review Checklist

- Confirm `source_url` points to the RBA F11.1 CSV.
- Confirm `retrieved_at` reflects the date the CSV was retrieved.
- Confirm `citation_detail` names the selected row and `FXRUSD` series.
- Run `python -m unittest discover -s tests`.
- Run the canonical calibration command and confirm currency assumptions appear in JSON and Markdown reports.
