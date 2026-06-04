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
    for rate in data["rates"]:
        validate_rate_metadata(rate)
    return data


def validate_rate_metadata(rate):
    required = {"id", "from", "to", "rate", "as_of", "source_name", "source_type", "evidence_type"}
    missing = required - set(rate)
    if missing:
        raise CurrencyConversionError(
            f"FX rate {rate.get('id', '<unknown>')} missing required fields: {', '.join(sorted(missing))}"
        )

    if rate["evidence_type"] == "source_backed":
        source_fields = {"source_url", "retrieved_at", "citation_detail"}
        missing_source_fields = source_fields - set(rate)
        if missing_source_fields:
            raise CurrencyConversionError(
                "Source-backed FX rate "
                f"{rate['id']} missing source metadata: {', '.join(sorted(missing_source_fields))}"
            )


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
        if normalize_currency(rate["from"]) == to_currency and normalize_currency(rate["to"]) == from_currency:
            return invert_rate(rate, from_currency, to_currency)

    raise CurrencyConversionError(f"No FX rate configured for {from_currency} to {to_currency}")


def invert_rate(rate, from_currency, to_currency):
    inverted = dict(rate)
    inverted["id"] = f"inverse:{rate['id']}"
    inverted["from"] = from_currency
    inverted["to"] = to_currency
    inverted["rate"] = 1 / float(rate["rate"])
    inverted["inverted_from_rate_id"] = rate["id"]
    inverted["notes"] = (
        f"Inverted from {rate['from']} to {rate['to']} source rate {rate['rate']}. "
        f"{rate.get('notes', '')}"
    ).strip()
    return inverted


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
        "source_url": rate.get("source_url"),
        "retrieved_at": rate.get("retrieved_at"),
        "citation_detail": rate.get("citation_detail"),
        "evidence_type": rate.get("evidence_type"),
        "inverted_from_rate_id": rate.get("inverted_from_rate_id"),
        "notes": rate.get("notes", ""),
    }


def normalize_currency(currency):
    if not currency:
        raise CurrencyConversionError("Currency is required for conversion")
    return str(currency).upper()
