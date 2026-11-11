"""Where a shard's maximum sits in a published loss distribution.

ADR-0008 gave a maximum a third declared axis — *what, if anything, is known
about being exceeded* — and recorded that most of the portfolio could answer
only `none_known`. The reason given, in `engine/exceedance.py` and in
`docs/FINDINGS.md` finding 3, was that no such distribution had been found:
*"We have not found one, publicly, anywhere."*

That was fair when written and was not revised. Cyentia's IRIS 2025 publishes
50th and 95th percentile losses by revenue tier (Table 1), and the report entered
the corpus on 2026-08-15 — eight days after ADR-0008, two days after finding 3.
`sources/audit.yaml` recorded it the same day as `verified_against_artifact`,
quoting the report's own 95th-percentile sentence, while the evidence record
citing that source kept `exceedance_basis: none_known` and a "not a formal
percentile" caveat. **The audit held the refutation of the finding for 88 days,
and nothing compared the two.** Table 1 itself neither surface had read.

This module does **not** re-anchor anything. It reports, for each published
shard, where the maximum it already uses falls against the published percentiles
for its own org profile's revenue tier. A bracket is a weaker statement than a
stated percentile and is deliberately not minted as a new `exceedance_basis`
value — see the ADR. What it buys is that a reader is told whether the number
they are treating as the outer bound is one the population routinely exceeds.

Like coherence and exceedance, this reads the **calibration-selected** anchors,
because those are the ones the simulation composes.
"""

import re
from pathlib import Path

from engine.currency import convert_currency, load_fx_rates
from engine.evidence import load_evidence_records
from engine.exceedance import module_exceedance
from engine.profiles import load_yaml_file
from engine.provenance import build_portfolio_provenance

#: The committed verbatim extract of IRIS 2025 Table 1. The numbers live here and
#: nowhere else in the repo, so a figure in prose cannot drift from its source.
TABLE_PATH = Path("extractions/cyentia_iris_2025_table1_loss_percentiles.txt")

#: The source whose distribution this is.
SOURCE_ID = "cyentia_iris_2025"
SOURCE_NAME = "Cyentia Information Risk Insights Study 2025, Table 1"

#: Loss percentiles are published in USD.
TABLE_CURRENCY = "USD"

_MAGNITUDE = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
_MONEY = re.compile(r"\$([\d,.]+)([KMB])")
_ROW = re.compile(r"^\s*(More than \$10B|\$1B to \$10B|\$100M to \$1B|Less than \$100M)\s+(.*)$")

#: Revenue bounds (USD) for each published tier, as the tier labels state them.
TIER_BOUNDS = {
    "More than $10B": (10_000_000_000, None),
    "$1B to $10B": (1_000_000_000, 10_000_000_000),
    "$100M to $1B": (100_000_000, 1_000_000_000),
    "Less than $100M": (None, 100_000_000),
}


def _money(text):
    match = _MONEY.match(text.strip())
    if not match:
        raise ValueError(f"not a published money figure: {text!r}")
    return float(match.group(1).replace(",", "")) * _MAGNITUDE[match.group(2)]


def load_tiers(path=None):
    """Parse the committed Table 1 extract into `{tier_label: {50: usd, 95: usd}}`.

    Raises if the artifact no longer holds all four published rows, so a silent
    truncation of the extract fails loudly rather than shrinking the table.
    """
    path = Path(path or TABLE_PATH)
    tiers = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = _ROW.match(line)
        if not row:
            continue
        figures = _MONEY.findall(row.group(2))
        if len(figures) != 2:
            continue
        p50, p95 = (_money(f"${value}{mag}") for value, mag in figures)
        tiers[row.group(1)] = {50: p50, 95: p95}
    if set(tiers) != set(TIER_BOUNDS):
        missing = sorted(set(TIER_BOUNDS) - set(tiers))
        raise ValueError(f"{path} is missing published tiers: {missing}")
    return tiers


def tier_for_revenue(revenue):
    """The published tier a given annual revenue (USD) falls in."""
    for label, (low, high) in TIER_BOUNDS.items():
        if (low is None or revenue >= low) and (high is None or revenue < high):
            return label
    raise ValueError(f"no published tier covers revenue {revenue!r}")


def _org_revenue(root, module_id):
    module = load_yaml_file(Path(root) / "risk_modules" / f"{module_id}.yaml")
    profile_path = (module.get("artifacts") or {}).get("org_profile")
    if not profile_path:
        return None, None
    profile = load_yaml_file(Path(root) / profile_path)
    return profile.get("annual_revenue_or_budget"), profile_path


def _bracket(usd, tier):
    if usd > tier[95]:
        return "above_p95"
    if usd >= tier[50]:
        return "between_p50_p95"
    return "below_p50"


#: What each bracket licenses a reader to conclude, in the source's own terms.
BRACKET_MEANING = {
    "above_p95": "fewer than 5% of incidents in this revenue tier exceed it",
    "between_p50_p95": "more than 5% of incidents in this revenue tier exceed it",
    "below_p50": "more than half of incidents in this revenue tier exceed it",
}


def build_portfolio_brackets(root=".", module_ids=None, tiers=None):
    """Every published shard's maximum, placed against its own revenue tier.

    Returns `{'modules': [...], 'totals': {...}}`. A module whose maximum carries
    no currency, or whose profile states no revenue, is returned with
    `bracket: None` and a `skipped` reason rather than dropped.
    """
    root = Path(root)
    tiers = tiers or load_tiers(root / TABLE_PATH)
    fx_rates = load_fx_rates(root / "calibrations" / "fx_rates.yaml")
    by_id = {record["id"]: record for record in load_evidence_records(root / "evidence")}
    portfolio = build_portfolio_provenance(root, module_ids=module_ids)

    modules = []
    counts = {name: 0 for name in BRACKET_MEANING}
    for module in portfolio.get("modules", []):
        module_id = module.get("module_id")
        revenue, profile_path = _org_revenue(root, module_id)
        for entry in module_exceedance(module):
            card = next(
                (c for c in module.get("cards", [])
                 if c.get("parameter") == entry["parameter"]), None
            )
            evidence_id = (card or {}).get("evidence_id")
            record = by_id.get(evidence_id, {})
            currency = record.get("currency")
            row = {
                "module_id": module_id,
                "parameter": entry["parameter"],
                "evidence_id": evidence_id,
                "exceedance_basis": entry["exceedance_basis"],
                "value": entry["value"],
                "currency": currency,
                "revenue": revenue,
                "org_profile": profile_path,
                "bracket": None,
                "skipped": None,
            }
            if revenue is None or not currency or entry["value"] is None:
                row["skipped"] = "no revenue on the org profile" if revenue is None \
                    else "maximum carries no currency"
                modules.append(row)
                continue
            if currency != TABLE_CURRENCY:
                converted = convert_currency(
                    entry["value"], currency, TABLE_CURRENCY, fx_rates)
                usd, row["fx_rate_id"] = converted["value"], converted["rate_id"]
            else:
                usd, row["fx_rate_id"] = float(entry["value"]), None
            tier_label = tier_for_revenue(revenue)
            tier = tiers[tier_label]
            bracket = _bracket(usd, tier)
            counts[bracket] += 1
            row.update(
                usd=usd,
                tier=tier_label,
                p50=tier[50],
                p95=tier[95],
                ratio_to_p95=usd / tier[95],
                bracket=bracket,
                meaning=BRACKET_MEANING[bracket],
            )
            modules.append(row)

    placed = sum(counts.values())
    return {
        "modules": modules,
        "totals": {
            "placed": placed,
            "by_bracket": counts,
            "at_or_below_p95": counts["between_p50_p95"] + counts["below_p50"],
            "source_id": SOURCE_ID,
        },
    }
