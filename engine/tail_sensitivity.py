"""Tail sensitivity: how much of a shard's answer rests on its maximum?

ADR-0008 commitment 2. The worked decision measured this by hand for one shard —
`docs/WORKED_DECISION_AU_RANSOMWARE_LIMIT.md` found the per-event mean running
14.8x its own mode, and P(event > AUD 20M) swinging 0% to 23% when only
`impact.max` moved. Every shard has the same shape, so the finding should be an
output, not an anecdote in one document.

Two readings, deliberately different in kind:

**Leverage is analytic, not simulated.** The engine composes `min`/`likely`/`max`
with a beta-PERT at the default confidence of 4, whose mean is exactly
`(min + 4*likely + max) / 6`. So the maximum's contribution to the per-event mean
is `max / (min + 4*likely + max)` — an identity, not an estimate, and it needs no
seed, no trials and no Monte Carlo error. `tests/test_tail_sensitivity.py` pins it
against the engine's own sampler so it cannot drift into fiction if the
distribution changes.

**Swing is simulated.** Leverage says how much of the mean comes from the maximum;
it says nothing about what a *decision* does. So the swing re-runs the real
seeded simulation with `impact.max` alone moved by a stated factor and reports
what the published annual figures do. The factor is a transparent stress on the
anchor, not a claim about the world.

Read either one next to the shard's `exceedance_basis` (ADR-0008 commitment 1).
High leverage on a maximum declared `none_known` is the combination that should
worry a reader: most of the answer resting on the one number that admits it
cannot say how often it is exceeded.
"""

import random

from engine.exceedance import module_exceedance
from engine.fair_calc import (
    SCHEMA_PATH,
    compute_stats,
    derive_scenario_seed,
    load_and_validate,
    load_schema,
    run_simulation,
)
from engine.provenance import build_portfolio_provenance
from engine.risk_modules import find_risk_module

#: The beta-PERT confidence the engine runs with (engine.fair_calc.beta_pert).
PERT_CONFIDENCE = 4

#: Published-run settings, so a swing is comparable to the numbers on the surfaces.
TRIALS = 10000
SEED = 42

#: How hard the swing stresses `impact.max`. Symmetric and stated, so a reader can
#: see it is an anchor stress rather than a forecast.
SWING_FACTORS = (0.5, 2.0)

#: Above this share of the per-event mean, the shard's answer is mostly its maximum.
LEVERAGE_CONCERN = 0.5


def pert_mean(low, likely, high, confidence=PERT_CONFIDENCE):
    """Mean of the beta-PERT the engine samples: `(min + c*likely + max) / (c + 2)`."""
    return (low + confidence * likely + high) / (confidence + 2)


def max_leverage(impact, confidence=PERT_CONFIDENCE):
    """Share of the per-event mean contributed by the `max` anchor.

    Exact for the engine's distribution: the PERT mean is a weighted sum of the three
    anchors, so the maximum's share of it is `max / (min + c*likely + max)`. Returns
    None when the range is degenerate.
    """
    if not impact:
        return None
    total = impact["min"] + confidence * impact["likely"] + impact["max"]
    if total <= 0:
        return None
    return impact["max"] / total


def _stats_for(config, trials=TRIALS, seed=SEED, scenario_path=None):
    scenario_seed = derive_scenario_seed(seed, scenario_path, config)
    _, results = run_simulation(config, trials, "pert", random.Random(scenario_seed))
    return compute_stats(results)


def module_tail_sensitivity(root, module_id, factors=SWING_FACTORS):
    """Leverage and swing for one shard, with its declared exceedance basis attached."""
    module = find_risk_module(module_id, root)
    scenario_path = root / (module.get("artifacts") or {})["scenario"]
    schema = load_schema(SCHEMA_PATH)
    config = load_and_validate(scenario_path, schema)
    impact = config["impact"]

    base = _stats_for(config, scenario_path=scenario_path)
    swings = []
    for factor in factors:
        moved = {
            **config,
            "impact": {**impact, "max": impact["max"] * factor},
        }
        stats = _stats_for(moved, scenario_path=scenario_path)
        swings.append(
            {
                "factor": factor,
                "impact_max": moved["impact"]["max"],
                "avg": stats["mean"],
                "p95": stats["p95"],
                "p99": stats["p99"],
                "avg_change": (stats["mean"] - base["mean"]) / base["mean"] if base["mean"] else None,
            }
        )

    # ADR-0008 commitment 1: the reason leverage matters is what the maximum admits.
    maxima = module_exceedance_for(root, module_id)
    return {
        "module_id": module_id,
        "currency": (config.get("metadata") or {}).get("currency"),
        "impact": dict(impact),
        "event_mean": pert_mean(impact["min"], impact["likely"], impact["max"]),
        "leverage": max_leverage(impact),
        "mean_over_mode": (
            pert_mean(impact["min"], impact["likely"], impact["max"]) / impact["likely"]
            if impact["likely"]
            else None
        ),
        "exceedance_basis": maxima[0]["exceedance_basis"] if maxima else None,
        "base": base,
        "swings": swings,
    }


def module_exceedance_for(root, module_id):
    """The shard's declared maxima, via the provenance layer the other axes use."""
    from engine.provenance import build_module_provenance

    return module_exceedance(build_module_provenance(module_id, root))


def build_portfolio_tail_sensitivity(root, module_ids=None, factors=SWING_FACTORS):
    """Tail sensitivity for every shard, ordered by leverage (most tail-driven first)."""
    portfolio = build_portfolio_provenance(root, module_ids=module_ids)
    rows = [
        module_tail_sensitivity(root, m["module_id"], factors=factors)
        for m in portfolio.get("modules", [])
    ]
    rows.sort(key=lambda r: (r["leverage"] is None, -(r["leverage"] or 0)))
    unquantified_and_leveraged = [
        r
        for r in rows
        if r["exceedance_basis"] == "none_known" and (r["leverage"] or 0) >= LEVERAGE_CONCERN
    ]
    return {
        "shards": rows,
        "totals": {
            "shards": len(rows),
            "mean_leverage": (sum(r["leverage"] or 0 for r in rows) / len(rows)) if rows else 0,
            "max_leverage": max((r["leverage"] or 0 for r in rows), default=0),
            "shards_majority_driven_by_max": sum(
                1 for r in rows if (r["leverage"] or 0) >= LEVERAGE_CONCERN
            ),
            "shards_majority_driven_by_an_unquantified_max": len(unquantified_and_leveraged),
        },
    }


def headline(totals):
    """The one sentence a reader should leave with."""
    return (
        f"{totals['shards_majority_driven_by_max']} of {totals['shards']} shards take most of "
        f"their modeled per-event loss from the `impact.max` anchor alone — and in "
        f"{totals['shards_majority_driven_by_an_unquantified_max']} of those the maximum "
        f"declares no exceedance probability at all."
    )


def format_portfolio_markdown(portfolio):
    """Human-readable tail-sensitivity report, mirroring the other two axes' reports."""
    totals = portfolio["totals"]
    lines = [
        "# Tail sensitivity report",
        "",
        "How much of a shard's answer rests on its maximum, and what the answer does when",
        "only that anchor moves. See [ADR-0008](adr/0008-the-governed-tail.md).",
        "",
        f"**{headline(totals)}**",
        "",
        "*Leverage* is analytic — the engine's beta-PERT mean is "
        "`(min + 4·likely + max) / 6`, so the maximum's share of it is exact, not sampled. "
        "*Swing* re-runs the published simulation (10,000 trials, seed 42) with `impact.max` "
        "alone moved by the stated factor: a transparent stress on the anchor, not a forecast.",
        "",
        "| Shard | Leverage | Mean ÷ mode | Exceedance | AVG at ½ max | AVG at 2× max |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in portfolio["shards"]:
        swings = {s["factor"]: s for s in row["swings"]}

        def change(factor):
            s = swings.get(factor)
            if not s or s["avg_change"] is None:
                return "—"
            return f"{s['avg_change']:+.0%}"

        lines.append(
            f"| `{row['module_id']}` | {row['leverage']:.0%} | "
            f"{row['mean_over_mode']:.1f}× | `{row['exceedance_basis'] or '—'}` | "
            f"{change(0.5)} | {change(2.0)} |"
        )
    lines.append("")
    lines.append(
        "A high leverage next to `none_known` is the combination to read carefully: most of "
        "the modeled loss is coming from the one anchor that admits it cannot say how often "
        "it is exceeded."
    )
    lines.append("")
    return "\n".join(lines)
