"""The loss-event registry: documented cyber loss events with typed amounts.

ADR-0012, superseding ADR-0005. A record describes **one organisation's one incident**,
not a cell — which is what makes it different in kind from everything in `evidence/`,
and why it lives in its own directory with its own schema.

The load-bearing rule is that **every amount is typed**. The corpus mixes gross event
costs with insurance recoveries, court settlements, revenue impacts and
period-over-period deltas, and a reader who sums them gets a number that means nothing.
`gross_event_amounts()` exists so that consumers have an obvious correct default and
have to opt in to the rest.

Two things this module deliberately does **not** provide, both forbidden by ADR-0012:

- **No aggregate.** There is no mean, median or total across events. The corpus is
  selection-biased toward listed entities and censored at each filer's own materiality
  threshold, so a central tendency computed from it would describe nothing.
- **No exceedance.** 36 heterogeneous events across many sectors and countries give no
  per-cell exceedance statistic. Ranking a maximum inside them would be a worse error
  than declaring `none_known`, which is what ADR-0008 already requires.

The registry is a **bounded trial** with a retirement test: if no shard cites an entry
and no outside contributor adds one within two release cycles, it is retired rather than
carried. `trial_metrics()` computes exactly those two numbers so the decision is made on
evidence rather than sentiment.
"""
import json
from pathlib import Path

import yaml

REGISTRY_DIRNAME = "loss_events"
SCHEMA_RELPATH = Path("schemas") / "loss_event_schema.json"

#: Amount types that are a cost or impact borne by the filer. Recoveries, settlements
#: and deltas are real and recorded, but they are not what an event cost.
GROSS_EVENT_TYPES = frozenset({"direct_cost", "total_event_impact", "revenue_impact"})

#: Types that must never be read as an event cost, kept explicit so the distinction is
#: legible at the call site rather than implied by absence.
NON_LOSS_TYPES = frozenset({"insurance_recovery", "legal_settlement", "period_delta"})


def load_loss_events(root):
    """Every registry record, in file then document order."""
    directory = Path(root) / REGISTRY_DIRNAME
    if not directory.is_dir():
        return []
    events = []
    for path in sorted(directory.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for event in payload.get("events", []):
            event = dict(event)
            event["_file"] = path.name
            events.append(event)
    return events


def validate_loss_events(root):
    """Structural + rule errors. Returns a list of strings; empty means clean.

    Schema validation runs when `jsonschema` is importable, but the rules below hold
    regardless, because they are the ones ADR-0012 actually turns on and a missing
    optional dependency must not silently disable them.
    """
    root = Path(root)
    errors = []
    events = load_loss_events(root)
    if not events:
        return errors

    schema_path = root / SCHEMA_RELPATH
    try:
        import jsonschema

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for path in sorted((root / REGISTRY_DIRNAME).glob("*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            try:
                jsonschema.validate(payload, schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"{path.name}: schema: {exc.message}")
    except ImportError:
        pass

    seen = {}
    for event in events:
        eid = event.get("id")
        if eid in seen:
            errors.append(f"{eid}: duplicate id (also in {seen[eid]})")
        seen[eid] = event.get("_file")

        amounts = event.get("amounts") or []
        if not amounts:
            errors.append(f"{eid}: no amounts — a record with no figure is not a loss event")
        for amount in amounts:
            if not (amount.get("cited_line") or "").strip():
                errors.append(f"{eid}: an amount has no cited_line")
            # The census hazard: statement tables are denominated in thousands, so a
            # bare figure under ~10,000 is either genuinely small or off by 1000x.
            # Either way it owes the reader an explicit note of where units came from.
            if amount.get("value", 0) < 10_000 and not amount.get("units_resolved_from"):
                errors.append(
                    f"{eid}: amount {amount.get('value')} is small enough to be a "
                    "thousands-denominated figure read at face value; it must declare "
                    "units_resolved_from"
                )
        if not (event.get("limitations") or "").strip():
            errors.append(f"{eid}: limitations must never be empty")
        verification = event.get("verification") or {}
        if verification.get("method") != "machine_candidate_human_confirmed":
            errors.append(f"{eid}: ADR-0012 forbids unverified extraction")
    return errors


def gross_event_amounts(event):
    """The amounts that are a cost or impact borne by the filer.

    Use this rather than `event['amounts']` unless you specifically want recoveries,
    settlements or deltas — and if you do, say so at the call site.
    """
    return [a for a in event.get("amounts", []) if a.get("type") in GROSS_EVENT_TYPES]


def registry_summary(root):
    """Counts for the doctor line and the README. Never an average — see the module docstring."""
    events = load_loss_events(root)
    amounts = [a for e in events for a in e.get("amounts", [])]
    by_type = {}
    for amount in amounts:
        by_type[amount["type"]] = by_type.get(amount["type"], 0) + 1
    return {
        "events": len(events),
        "amounts": len(amounts),
        "amounts_by_type": by_type,
        "non_loss_amounts": sum(1 for a in amounts if a.get("type") in NON_LOSS_TYPES),
        "entities": len({(e.get("entity") or {}).get("name") for e in events}),
        "countries": sorted({(e.get("entity") or {}).get("country") for e in events if e.get("entity")}),
        "events_with_a_gross_amount": sum(1 for e in events if gross_event_amounts(e)),
    }


def trial_metrics(root):
    """The two numbers ADR-0012's kill criterion is decided on.

    `shards_citing_a_registry_entry` — how many shards anchor `impact.max` on a registry
    id rather than a one-off. `external_contributions` cannot be derived from the tree
    and is None until someone records it; None means unmeasured, not zero.
    """
    root = Path(root)
    ids = {e["id"] for e in load_loss_events(root)}
    citing = set()
    if ids:
        for path in sorted((root / "calibrations").glob("*.yaml")):
            text = path.read_text(encoding="utf-8")
            if any(eid in text for eid in ids):
                citing.add(path.stem)
    return {
        "registry_events": len(ids),
        "shards_citing_a_registry_entry": len(citing),
        "citing_shards": sorted(citing),
        "external_contributions": None,
    }

#: Exceedance bases that say something about being exceeded. A registry entry carries
#: none of these by rule, so replacing an anchor that has one is a regression.
INFORMATIVE_EXCEEDANCE = frozenset({"observed_rank", "modeled_quantile"})


def citation_candidates(root):
    """Could any shard's `impact.max` legitimately cite a registry entry?

    The other half of ADR-0012's kill criterion is "no shard cites an entry", and that
    number is worthless without knowing whether any shard *could*. Zero citations
    because nothing fits is a different result from zero citations because nobody
    bothered, and only the second is a reason to retire the registry.

    A candidate must match the shard's country **and** threat and carry a gross amount.
    Even then it is `blocked` when the shard's current maximum already carries an
    informative exceedance basis: swapping a maximum that says how often it is exceeded
    for one that says nothing would lose information, which ADR-0008 exists to prevent.
    """
    import yaml

    root = Path(root)
    records = {}
    for path in sorted((root / "evidence").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for record in payload.get("records", []):
            records[record["id"]] = record

    events = load_loss_events(root)
    out = []
    for path in sorted((root / "risk_modules").glob("*.yaml")):
        module = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        calibration_path = (module.get("artifacts") or {}).get("calibration")
        if not calibration_path:
            continue
        profile = yaml.safe_load((root / calibration_path).read_text(encoding="utf-8")) or {}
        maximum = ((profile.get("parameters") or {}).get("impact") or {}).get("max") or {}
        anchor = records.get(maximum.get("evidence_id"), {})
        context = module.get("context") or {}
        matches = [
            event for event in events
            if (event.get("entity") or {}).get("country") == context.get("country")
            and (event.get("event") or {}).get("threat") == module.get("threat")
            and gross_event_amounts(event)
        ]
        exceedance = anchor.get("exceedance_basis")
        blocked = bool(matches) and exceedance in INFORMATIVE_EXCEEDANCE
        out.append({
            "shard": module.get("id"),
            "country": context.get("country"),
            "threat": module.get("threat"),
            "current_exceedance": exceedance,
            "candidates": [event["id"] for event in matches],
            "industry_matched": [
                event["id"] for event in matches
                if (event.get("entity") or {}).get("industry") == context.get("industry")
            ],
            "blocked_by_exceedance_loss": blocked,
            "citable": bool(matches) and not blocked,
        })
    return out
