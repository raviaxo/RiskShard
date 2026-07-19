"""Frequency backtesting against open incident data.

Checks a shard's frequency model against the VERIS Community Database (VCDB), an
open incident corpus. The honest scope is FREQUENCY ONLY: VCDB populates a dollar
impact on ~5% of incidents, so severity is not recoverable here (see the
frequency/severity asymmetry in docs/METHODOLOGY.md).

Design: IO (download/unzip) is isolated in ``load_vcdb_records``; everything else
is pure functions over a list of incident dicts, so the analysis is testable on
fixed inputs. No third-party dependency — stdlib ``urllib``/``zipfile``/``json``
and ``math`` only. VCDB is CC BY-SA 4.0.
"""

import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VCDB_URL = "https://raw.githubusercontent.com/vz-risk/VCDB/master/data/joined/vcdb.json.zip"
VCDB_LICENSE = "CC BY-SA 4.0"
DEFAULT_CACHE = PROJECT_ROOT / "sources" / "raw" / "vcdb.json.zip"
FINANCE_NAICS_PREFIX = "52"


# ---------------------------------------------------------------------------
# IO (isolated, not covered by the pure-function tests)
# ---------------------------------------------------------------------------

def load_vcdb_records(cache_path=DEFAULT_CACHE, url=VCDB_URL, allow_download=True):
    """Return (records, provenance). Fetch-if-missing into the ignored cache."""
    cache_path = Path(cache_path)
    if not cache_path.exists():
        if not allow_download:
            raise FileNotFoundError(f"VCDB cache missing and download disabled: {cache_path}")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "riskshard-backtest"})
        with urllib.request.urlopen(request) as response:
            cache_path.write_bytes(response.read())

    payload = cache_path.read_bytes()
    records = _read_zip_json(payload)
    provenance = {
        "dataset": "VERIS Community Database (VCDB)",
        "url": url,
        "license": VCDB_LICENSE,
        "sha256": _sha256(payload),
        "archive_bytes": len(payload),
        "record_count": len(records),
    }
    return records, provenance


def _read_zip_json(payload):
    archive = zipfile.ZipFile(io.BytesIO(payload))
    name = next(n for n in archive.namelist() if n.endswith(".json"))
    data = json.loads(archive.read(name))
    if isinstance(data, dict):
        data = data.get("incidents", data)
    return data


def _sha256(payload):
    import hashlib

    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# Pure functions over incident dicts
# ---------------------------------------------------------------------------

def incident_country(record):
    country = record.get("victim", {}).get("country") or []
    if isinstance(country, list):
        return country[0] if country else None
    return country


def incident_naics2(record):
    return str(record.get("victim", {}).get("industry") or "")[:2]


def incident_year(record):
    year = record.get("timeline", {}).get("incident", {}).get("year")
    return year if isinstance(year, int) else None


def is_breach(record):
    # A confidentiality attribute means data was at least at risk / disclosed.
    return "confidentiality" in (record.get("attribute") or {})


def filter_cell(records, country, naics_prefix=FINANCE_NAICS_PREFIX,
                breach_only=True, since_year=None):
    """Select incidents for one country/industry cell."""
    selected = []
    for record in records:
        if country is not None and incident_country(record) != country:
            continue
        if naics_prefix is not None and not incident_naics2(record).startswith(naics_prefix):
            continue
        if breach_only and not is_breach(record):
            continue
        if since_year is not None:
            year = incident_year(record)
            if year is None or year < since_year:
                continue
        selected.append(record)
    return selected


def annual_counts(records, since_year=None, through_year=None):
    """Map each year in range to its incident count (zero-filled across the span)."""
    years = [incident_year(r) for r in records]
    years = [y for y in years if y is not None]
    if not years:
        return {}
    lo = since_year if since_year is not None else min(years)
    hi = through_year if through_year is not None else max(years)
    counts = {year: 0 for year in range(lo, hi + 1)}
    for year in years:
        if lo <= year <= hi:
            counts[year] += 1
    return counts


def dispersion_stats(counts):
    """Poisson-vs-overdispersion diagnostic for a year->count mapping."""
    values = list(counts.values())
    n = len(values)
    if n == 0:
        return {"n_years": 0, "mean": 0.0, "variance": 0.0, "dispersion_index": None,
                "verdict": "no_data"}
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else 0.0
    dispersion = (variance / mean) if mean > 0 else None
    # Dispersion index (variance/mean) ~1 => Poisson-consistent; >>1 => overdispersed
    # (negative-binomial fits better; a smooth PERT rate understates year-to-year swing).
    if dispersion is None:
        verdict = "no_events"
    elif dispersion < 1.5:
        verdict = "poisson_consistent"
    elif dispersion < 3.0:
        verdict = "mild_overdispersion"
    else:
        verdict = "strong_overdispersion"
    return {"n_years": n, "mean": mean, "variance": variance,
            "dispersion_index": dispersion, "verdict": verdict}


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _poisson_logpmf(k, lam):
    if lam <= 0:
        return 0.0 if k == 0 else float("-inf")
    return -lam + k * math.log(lam) - math.lgamma(k + 1)


def _negbin_logpmf(k, r, p):
    # r = dispersion/size (>0), p = success prob (0<p<1); mean = r*(1-p)/p.
    if not (0 < p < 1) or r <= 0:
        return float("-inf")
    return (math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
            + r * math.log(p) + k * math.log(1 - p))


def negbin_mom(counts):
    """Method-of-moments negative-binomial fit for a year->count mapping.

    Returns ``None`` when the data is not overdispersed (variance <= mean), where
    a negative-binomial does not apply and Poisson is the honest model.
    """
    values = list(counts.values())
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    if mean <= 0 or variance <= mean:
        return None
    p = mean / variance
    r = mean ** 2 / (variance - mean)
    return {"r": r, "p": p, "mean": mean, "variance": variance}


def fit_comparison(counts):
    """Compare Poisson vs. negative-binomial fit on annual counts (log-likelihood).

    The negative-binomial has one extra parameter, so it fits at least as well
    whenever the data is overdispersed; the informative outputs are the size
    parameter ``r`` (smaller = more clustered) and the log-likelihood gain, not
    the mere fact that NB wins. Reported honestly with that caveat.
    """
    values = list(counts.values())
    n = len(values)
    if n < 2:
        return {"comparable": False, "reason": "need_at_least_2_years"}
    mean = sum(values) / n
    poisson_ll = sum(_poisson_logpmf(k, mean) for k in values)
    nb = negbin_mom(counts)
    if nb is None:
        return {
            "comparable": True,
            "overdispersed": False,
            "poisson_loglik": poisson_ll,
            "negbin": None,
            "better_fit": "poisson",
            "note": "Not overdispersed (variance <= mean); Poisson is the honest model.",
        }
    nb_ll = sum(_negbin_logpmf(k, nb["r"], nb["p"]) for k in values)
    return {
        "comparable": True,
        "overdispersed": True,
        "poisson_loglik": poisson_ll,
        "negbin_loglik": nb_ll,
        "negbin": nb,
        "loglik_gain": nb_ll - poisson_ll,
        "better_fit": "negbin" if nb_ll > poisson_ll else "poisson",
        "note": (
            "Negative-binomial has one extra parameter, so it is expected to fit "
            "better under overdispersion; size r (smaller = more clustered) and "
            "the log-likelihood gain quantify how far the counts depart from a "
            "smooth Poisson/PERT rate."
        ),
    }


def order_of_magnitude_bracket(shard_frequency, observed_rate):
    """Directional check: does the shard's frequency band bracket an observed
    per-firm rate within an order of magnitude? Returns a verdict dict.
    """
    lo = shard_frequency["min"]
    hi = shard_frequency["max"]
    within_band = lo <= observed_rate <= hi
    # order-of-magnitude tolerance around the band
    within_om = (lo / 10.0) <= observed_rate <= (hi * 10.0)
    return {
        "shard_band": [lo, shard_frequency["likely"], hi],
        "observed_rate": observed_rate,
        "within_band": within_band,
        "within_order_of_magnitude": within_om,
    }


def analyze_cell(records, country, since_year, naics_prefix=FINANCE_NAICS_PREFIX):
    cell = filter_cell(records, country, naics_prefix=naics_prefix,
                       breach_only=True, since_year=since_year)
    counts = annual_counts(cell, since_year=since_year)
    return {
        "country": country,
        "since_year": since_year,
        "incident_count": len(cell),
        "annual_counts": counts,
        "dispersion": dispersion_stats(counts),
        "fit": fit_comparison(counts),
    }


def build_frequency_backtest_report(records, provenance, shard_id, shard_frequency,
                                    primary_country, secondary_country,
                                    since_year, firms=None):
    """Assemble the frequency backtest. ``shard_frequency`` is the primary cell's
    shard frequency band; ``firms`` is an optional, explicitly-labeled external
    denominator (count of firms in the primary cell) for a per-firm rate check.
    """
    primary = analyze_cell(records, primary_country, since_year)
    secondary = analyze_cell(records, secondary_country, since_year)

    likely = shard_frequency["likely"]
    mean_count = primary["dispersion"]["mean"]
    # Denominator-free framing: how many firms would VCDB have to be "covering"
    # for its observed count to match the shard's rate? Absurdly small => VCDB
    # massively undercounts, so it cannot calibrate an absolute rate (only floor).
    implied_covered_firms = (mean_count / likely) if likely > 0 else None

    rate_check = None
    if firms:
        rate_check = order_of_magnitude_bracket(shard_frequency, mean_count / firms)

    return {
        "report_type": "riskshard_frequency_backtest",
        "provenance": provenance,
        "scope": "frequency_only",
        "severity_note": (
            "VCDB populates a dollar impact on ~5% of incidents; severity is not "
            "backtested here. See docs/METHODOLOGY.md (frequency/severity asymmetry)."
        ),
        "shard_id": shard_id,
        "shard_frequency": shard_frequency,
        "primary_cell": primary,
        "secondary_cell": secondary,
        "implied_covered_firms": implied_covered_firms,
        "denominator_firms": firms,
        "rate_check": rate_check,
    }


def format_frequency_backtest_report(report):
    prov = report["provenance"]
    primary = report["primary_cell"]
    secondary = report["secondary_cell"]
    freq = report["shard_frequency"]

    lines = [
        "RiskShard frequency backtest (VCDB)",
        f"Dataset : {prov['dataset']} ({prov['license']})",
        f"Archive : {prov['sha256'][:12]} / {prov['record_count']} incidents",
        f"Scope   : FREQUENCY ONLY -- {report['severity_note']}",
        "",
        f"Shard   : {report['shard_id']}",
        f"  frequency band (per firm-year): {freq['min']} / {freq['likely']} / {freq['max']}",
        "",
        f"Primary cell (the shard's cell): {primary['country']} finance breaches since {primary['since_year']}",
        f"  incidents: {primary['incident_count']} over {primary['dispersion']['n_years']} years "
        f"(mean {primary['dispersion']['mean']:.2f}/yr)",
        f"  PERT-vs-Poisson: dispersion index = {_fmt(primary['dispersion']['dispersion_index'])} "
        f"-> {primary['dispersion']['verdict']}",
        f"  {_fmt_fit(primary['fit'])}",
        "",
        f"Secondary cell (method check at depth): {secondary['country']} finance breaches since {secondary['since_year']}",
        f"  incidents: {secondary['incident_count']} over {secondary['dispersion']['n_years']} years "
        f"(mean {secondary['dispersion']['mean']:.2f}/yr)",
        f"  PERT-vs-Poisson: dispersion index = {_fmt(secondary['dispersion']['dispersion_index'])} "
        f"-> {secondary['dispersion']['verdict']}",
        f"  {_fmt_fit(secondary['fit'])}",
        "",
        "Denominator honesty",
        f"  Implied firms VCDB would 'cover' if its count matched the shard rate: "
        f"{_fmt(report['implied_covered_firms'], 1)}",
        "  If that is far below the real population, VCDB undercounts massively and",
        "  cannot calibrate an absolute rate -- treat its counts as a floor only.",
    ]
    if report["rate_check"]:
        rc = report["rate_check"]
        lines.extend([
            "",
            f"Per-firm rate check (denominator = {report['denominator_firms']} firms, LABELED ASSUMPTION)",
            f"  observed rate ~ {rc['observed_rate']:.4g}/firm-yr vs shard band "
            f"[{rc['shard_band'][0]}, {rc['shard_band'][2]}]",
            f"  within band: {rc['within_band']}; within order of magnitude: "
            f"{rc['within_order_of_magnitude']}",
        ])
    else:
        lines.extend([
            "",
            "Per-firm rate check: skipped (no --firms denominator supplied).",
        ])
    return "\n".join(lines) + "\n"


def _fmt(value, digits=2):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _fmt_fit(fit):
    if not fit.get("comparable"):
        return f"NB fit: n/a ({fit.get('reason')})"
    if not fit.get("overdispersed"):
        return "NB fit: not overdispersed; Poisson is the honest model."
    nb = fit["negbin"]
    return (
        f"NB fit: size r={_fmt(nb['r'])} (smaller = more clustered), "
        f"loglik gain over Poisson = {_fmt(fit['loglik_gain'])} -> {fit['better_fit']} fits better"
    )
