from pathlib import Path

from engine.profiles import load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FX_RATES_PATH = PROJECT_ROOT / "calibrations" / "fx_rates.yaml"


class CurrencyConversionError(ValueError):
    pass


def load_fx_rates(path=DEFAULT_FX_RATES_PATH):
    data = load_yaml_file(path)
    if not isinstance(data.get("rates"), list):
        raise CurrencyConversionError("FX rates file must contain a rates list")
    return data


def find_rate(fx_rates, from_currency, to_currency):
    from_currency = normalize_currency(from_currency)
    to_currency = normalize_currency(to_currency)

    if from_currency == to_currency:
        return {
            "id": "identity",
            "from": from_currency,
            "to": to_currency,
            "rate": 1.0,
            "as_of": None,
            "source_name": "No conversion",
            "source_type": "identity",
            "evidence_type": "source_backed",
            "notes": "Source and target currency are the same.",
        }

    for rate in fx_rates["rates"]:
        if normalize_currency(rate["from"]) == from_currency and normalize_currency(rate["to"]) == to_currency:
            return rate

    raise CurrencyConversionError(f"No FX rate configured for {from_currency} to {to_currency}")


def convert_currency(value, from_currency, to_currency, fx_rates):
    rate = find_rate(fx_rates, from_currency, to_currency)
    converted_value = value * float(rate["rate"])

    return {
        "value": converted_value,
        "from_currency": normalize_currency(from_currency),
        "to_currency": normalize_currency(to_currency),
        "rate": float(rate["rate"]),
        "rate_id": rate["id"],
        "as_of": rate.get("as_of"),
        "source_name": rate.get("source_name"),
        "source_type": rate.get("source_type"),
        "evidence_type": rate.get("evidence_type"),
        "notes": rate.get("notes", ""),
    }


def normalize_currency(currency):
    if not currency:
        raise CurrencyConversionError("Currency is required for conversion")
    return str(currency).upper()
