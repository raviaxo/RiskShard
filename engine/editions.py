"""Is a parameter anchored on an edition that a newer registered edition supersedes?

[`docs/CROSS_SOURCE.md`](../docs/CROSS_SOURCE.md) states the rule this module enforces,
in its own words:

> A figure's vintage matters at least as much as its geography, and a two-year-old
> number is not a slightly stale version of today's — it may be a different order of
> magnitude.

It states that beside a table showing Australia's median ransom demand moving from
$217,000 to $1.34 million in one year. Meanwhile a shard could be anchored on the
older edition of the very source that table is built from, and nothing would say so:
the registry knows both editions, the evidence record names one, and the two facts
have never been compared.

**This reports candidates, never verdicts.** A later edition is not automatically a
better anchor — it may change construct, drop the country cut, or restate over a
different population, and ADR-0007 says which mixes are acceptable is unresolved. So
the output is "these two look like editions of one series, and the parameter cites the
earlier one", which is a question for a person. Acting on it is parameter movement and
belongs to the owner ([ADR-0016](../docs/adr/0016-the-audit-is-the-product.md) part 2
maintains shards for correctness only).

**Matching is deliberately conservative.** Same publisher, and a title that reduces to
the same stem once edition years and packaging words are removed — so *The State of
Ransomware in Australia 2025 (whitepaper)* and *The State of Ransomware in Australia
2026* pair, while the manufacturing sector cut does not pair with a country cut. A
missed pair costs a reminder; a false pair costs trust in the whole check, which is
why the bias runs that way.
"""
import re
from pathlib import Path

import yaml

from engine.provenance import build_portfolio_provenance
from engine.source_audit import load_registry

#: Words that describe the packaging of an edition rather than what it measures.
PACKAGING = frozenset({
    "whitepaper", "report", "the", "a", "an", "of", "in", "and", "for",
    "edition", "annual", "study", "survey", "global",
    # How *we* stored a copy is never what it measures. Without these, the 2023 and
    # 2024 globals ("archived snapshot") failed to pair with the 2026 global, and the
    # check under-reported in silence — the failure mode this module is most exposed
    # to, because an empty result reads as "nothing is stale".
    "archived", "snapshot", "cut", "country",
})
YEAR = re.compile(r"\b(19|20)\d{2}\b")
WORD = re.compile(r"[a-z0-9]+")


def title_stem(title):
    """A title reduced to the tokens that say what was measured, not which year.

    Years go first — they are the edition marker and the whole point is to see past
    them. Packaging words go next, because "(whitepaper)" on one edition and not the
    next is a publishing decision, not a change of subject. What remains is sorted so
    word order cannot separate two spellings of the same series.
    """
    cleaned = YEAR.sub(" ", (title or "").lower())
    tokens = [w for w in WORD.findall(cleaned) if w not in PACKAGING]
    return tuple(sorted(tokens))


def edition_groups(registry):
    """Registered sources grouped into apparent series: same publisher, same stem."""
    groups = {}
    for source in registry:
        stem = title_stem(source.get("title"))
        if not stem:
            continue
        groups.setdefault(((source.get("publisher") or "").lower(), stem), []).append(source)
    return {k: sorted(v, key=lambda s: str(s.get("publication_date") or ""))
            for k, v in groups.items() if len(v) > 1}


def superseded_anchors(root):
    """Parameters citing an edition that a later registered edition appears to succeed.

    Returns one row per (parameter, newer edition) pair. `gap_days` is reported so a
    six-week overlap and a three-year lag are not presented as the same concern.
    """
    registry = load_registry(root)
    by_id = {s.get("id"): s for s in registry}
    groups = edition_groups(registry)
    later = {}
    for members in groups.values():
        for i, source in enumerate(members):
            successors = members[i + 1:]
            if successors:
                later[source.get("id")] = successors

    source_of = _source_by_evidence_id(root)
    rationales = _calibration_rationales(root)
    rows = []
    for module in build_portfolio_provenance(root)["modules"]:
        for card in module.get("cards") or []:
            cited = source_of.get(card.get("evidence_id"))
            for successor in later.get(cited, []):
                rows.append({
                    "module_id": module["module_id"],
                    "parameter": card.get("parameter"),
                    "evidence_id": card.get("evidence_id"),
                    "cites": cited,
                    "cites_date": str(by_id.get(cited, {}).get("publication_date") or ""),
                    "superseded_by": successor.get("id"),
                    "successor_date": str(successor.get("publication_date") or ""),
                    "successor_title": successor.get("title"),
                    # Why this anchor was chosen, in the calibration's own words.
                    # Carried because an older edition is often deliberate — a stress
                    # bound wants a *different* reading, not a newer one — and a check
                    # that presents a considered choice as a defect gets ignored.
                    "rationale": rationales.get((module["module_id"], card.get("parameter"))),
                })
    rows.sort(key=lambda r: (r["module_id"], r["parameter"] or ""))
    return rows


def _source_by_evidence_id(root):
    """Every evidence record's declared `source_id`, keyed by record id.

    The provenance card does not carry `source_id` — it carries `source_name`, which
    is a display string. Matching on that string is what the first version of this
    module did, and it silently missed the Australia pair: the record says
    "Sophos The State of Ransomware in Australia 2025" and the registry title is
    "The State of Ransomware in Australia 2025 (whitepaper)". A near-match that fails
    quietly is worse than no check, because the empty result reads as "nothing stale".
    So this reads the declared link instead of inferring one.
    """
    index = {}
    for path in sorted((Path(root) / "evidence").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for record in data.get("records") or []:
            if record.get("id") and record.get("source_id"):
                index[record["id"]] = record["source_id"]
    return index


def _calibration_rationales(root):
    """Each parameter's stated reason for its anchor, keyed by (module, parameter).

    Read from `calibrations/`, which is where the choice is actually justified. The
    Australia shard's `frequency.max` cites a 2023 edition on purpose — *"prior-year
    Australian reading as a genuinely distinct stress bound above the likely anchor"* —
    and reading that beside the flag is the difference between a useful check and a
    nag.
    """
    out = {}
    for module in build_portfolio_provenance(root)["modules"]:
        module_id = module["module_id"]
        for path in sorted((Path(root) / "calibrations").glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for family, slots in (data.get("parameters") or {}).items():
                for slot, spec in (slots or {}).items():
                    key = (module_id, f"{family}.{slot}")
                    if key in out or not isinstance(spec, dict):
                        continue
                    evidence_id = spec.get("evidence_id")
                    if evidence_id and any(c.get("evidence_id") == evidence_id
                                           for c in module.get("cards") or []):
                        out[key] = spec.get("rationale")
    return out
