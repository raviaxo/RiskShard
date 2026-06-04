#!/usr/bin/env python3
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RBA_F11_1_CSV_URL = "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Refresh sourced FX assumptions from RBA F11.1.")
    parser.add_argument("--input-csv", type=Path, help="Optional local RBA F11.1 CSV fixture.")
    parser.add_argument(
        "--output",
        default=ROOT / "calibrations" / "fx_rates.yaml",
        type=Path,
        help="FX rates YAML path to write.",
    )
    parser.add_argument("--as-of", help="Optional DD-Mon-YYYY row date to select.")
    parser.add_argument(
        "--retrieved-at",
        default=datetime.now(timezone.utc).date().isoformat(),
        help="Retrieval date to record as YYYY-MM-DD.",
    )
    return parser.parse_args()


def load_csv_text(input_csv=None):
    if input_csv:
        return Path(input_csv).read_text(encoding="utf-8-sig")

    request = Request(
        RBA_F11_1_CSV_URL,
        headers={
            "User-Agent": "RiskShardFXUpdater/0.1 (+https://github.com/raviaxo/RiskShard)",
            "Accept": "text/csv,*/*",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8-sig")


def parse_aud_usd_rate(csv_text, as_of=None):
    rows = list(csv.reader(csv_text.splitlines()))
    if not rows or rows[0][0] != "Title":
        raise ValueError("RBA F11.1 CSV must start with a Title row")

    try:
        aud_usd_index = rows[0].index("A$1=USD")
    except ValueError as exc:
        raise ValueError("RBA F11.1 CSV missing A$1=USD column") from exc

    selected = None
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        try:
            datetime.strptime(row[0], "%d-%b-%Y")
        except ValueError:
            continue
        if aud_usd_index >= len(row) or not row[aud_usd_index]:
            continue
        if as_of is None or row[0] == as_of:
            selected = row

    if selected is None:
        raise ValueError(f"No AUD/USD rate found for {as_of or 'latest date'}")

    row_date = datetime.strptime(selected[0], "%d-%b-%Y").date().isoformat()
    return row_date, float(selected[aud_usd_index])


def build_aud_usd_rate(row_date, aud_usd_rate, retrieved_at):
    return {
        "id": f"aud_to_usd_rba_f11_1_{row_date.replace('-', '_')}",
        "from": "AUD",
        "to": "USD",
        "rate": aud_usd_rate,
        "as_of": row_date,
        "source_name": "Reserve Bank of Australia Statistical Table F11.1",
        "source_type": "official_statistical_table",
        "source_url": RBA_F11_1_CSV_URL,
        "retrieved_at": retrieved_at,
        "citation_detail": (
            "F11.1 Exchange Rates, series FXRUSD, "
            f"row {row_date}; table quotes A$1=USD {aud_usd_rate}."
        ),
        "evidence_type": "source_backed",
        "notes": (
            "RBA F11.1 quotes AUD to USD. USD to AUD calibration conversions "
            "invert this rate and disclose the source rate ID in the calibration report."
        ),
    }


def build_fx_rates(row_date, aud_usd_rate, retrieved_at, existing_rates=None):
    aud_rate = build_aud_usd_rate(row_date, aud_usd_rate, retrieved_at)
    preserved_rates = [
        rate for rate in existing_rates or []
        if not is_rba_aud_usd_rate(rate)
    ]
    return {"rates": [aud_rate, *preserved_rates]}


def is_rba_aud_usd_rate(rate):
    return (
        str(rate.get("id", "")).startswith("aud_to_usd_rba_f11_1_")
        and rate.get("from") == "AUD"
        and rate.get("to") == "USD"
    )


def load_existing_rates(output_path):
    output_path = Path(output_path)
    if not output_path.exists():
        return []
    payload = yaml.safe_load(output_path.read_text()) or {}
    return payload.get("rates") or []


def write_fx_rates(data, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return output_path


def main():
    args = parse_args()
    csv_text = load_csv_text(args.input_csv)
    row_date, aud_usd_rate = parse_aud_usd_rate(csv_text, args.as_of)
    existing_rates = load_existing_rates(args.output)
    output_path = write_fx_rates(
        build_fx_rates(row_date, aud_usd_rate, args.retrieved_at, existing_rates),
        args.output,
    )
    print(f"FX rates written: {output_path}")
    print(f"AUD/USD {row_date}: {aud_usd_rate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
