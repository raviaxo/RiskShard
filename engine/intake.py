"""Intake triage: which obtained documents are worth reading, and in what order.

This is the layer *before* the source audit and the evidence corpus. A document
arrives, and the only questions that matter are whether it plausibly speaks to a
cell we actually model and whether reading it could move a number. Most cannot,
and saying so cheaply is the point — 67 documents arrived at once, and reading all
of them in arrival order would spend the same effort on a cloud-security vendor's
AI report as on a country-specific ransomware study that maps onto three shards.

**Intake scores promise, never content.** It reads a title and a first page and asks
*"could this serve cell X?"* — a question about scope, not findings.
[ADR-0015](../docs/adr/0015-the-source-audit.md) governs what a source *publishes*,
and that requires reading it. Nothing here may be quoted as a claim about a source;
a high intake score means "read this first", and a low one means "not now", and
neither means the document is good or bad.

The ranking is grounded in the portfolio's own measured gaps rather than in taste.
Sector is worth more than country in the current corpus because sector is bridged 49
times and country 15 — so a sector-specific study is worth more than another national
survey, and the numbers say so rather than the author.
"""
import json
import re
from pathlib import Path

import yaml

INTAKE_RELPATH = Path("sources") / "intake.yaml"

# Cell vocabulary, matched against a document's title and first page.
COUNTRY_WORDS = {
    "AU": ("australia", "australian"), "CA": ("canada", "canadian"),
    "DE": ("germany", "german", "deutschland"), "FR": ("france", "french", "français"),
    "GB": ("united kingdom", "uk ", " uk", "britain", "british"),
    "JP": ("japan", "japanese"), "SG": ("singapore",), "US": ("united states", " u.s.", "usa"),
}
SECTOR_WORDS = {
    "financial_services": ("financial services", "finance", "banking", "insurance"),
    "manufacturing": ("manufacturing", "industrial", "production"),
}
THREAT_WORDS = {
    "ransomware": ("ransomware",),
    "data_breach": ("data breach", "breach report", "personal data breach"),
    "business_email_compromise": ("business email compromise", "bec ", "payments fraud",
                                  "funds transfer", "scam"),
    "insider_misuse": ("insider",),
    "third_party_outage": ("supply chain", "third party", "third-party", "outage"),
}
# What a document must plausibly carry to move anything at all.
QUANTITY_WORDS = {
    "loss_magnitude": ("cost", "loss", "ransom paid", "claim", "damage", "impact"),
    "frequency": ("prevalence", "percent of organi", "rate", "how many", "experienced"),
    "exceedance": ("percentile", "distribution", "quantile", "top 5%"),
}


def load_intake(root):
    path = Path(root) / INTAKE_RELPATH
    if not path.exists():
        return []
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("intake") or []


def portfolio_gaps(root):
    """What the shards are actually short of, measured — the weighting behind the score.

    Returned as facet -> count of bridged parameter-instances, plus the set of cells
    in play. A candidate is worth more when it speaks to a facet the corpus is most
    short of, which stops the ranking being a matter of opinion.
    """
    from engine.provenance import build_portfolio_provenance

    prov = build_portfolio_provenance(root)
    facets, cells = {}, []
    for module in prov["modules"]:
        cell = module["cell"]
        cells.append({k: cell.get(k) for k in ("country", "industry", "company_size", "threat")})
        for card in module["cards"]:
            if not card.get("resolved"):
                continue
            for facet in (card.get("population") or {}).get("bridged_on") or []:
                facets[facet] = facets.get(facet, 0) + 1
    return {"bridged_by_facet": facets, "cells": cells}


def _hits(text, words):
    low = text.lower()
    return [key for key, terms in words.items() if any(t in low for t in terms)]


def scope_text(filename, title):
    """What a document *declares itself to be* — the only text intake should judge on.

    The first version of this scored keyword hits across the first 6,000 characters of
    body text and ranked a cloud identity-security report above sixteen country-specific
    ransomware studies, because the identity report's front matter happened to list every
    country its survey covered. Front matter is not scope.

    A filename and a title are a document's own claim about what it is, they are short
    enough that a hit means something, and for this corpus they are unusually reliable:
    `sophos-state-of-ransomware-in-japan-2026.pdf` says precisely which cell it speaks to.
    """
    return f"{filename.replace('-', ' ').replace('_', ' ')} || {title}"


def assess(scope, body, gaps):
    """Score one candidate's promise against the measured gaps.

    Two texts, deliberately, because the two questions have different evidence.
    **Scope** — which cell does it speak to — is judged on the filename and title, a
    document's own claim about itself. **Quantity** — could it carry a number at all —
    is judged on the body, because no filename advertises the word "cost".

    Getting that split wrong broke this scorer twice in a row and both failures are
    instructive. Scoring scope on the body ranked a cloud identity report above sixteen
    country-specific ransomware studies, on front matter that listed survey countries.
    Then scoring quantity on the filename zeroed those same sixteen, because
    `sophos-state-of-ransomware-in-japan-2026.pdf` does not say "cost" — a rule meant to
    drop documents that cannot move a number instead dropped the ones that could.

    Weighted by what the corpus is short of rather than by what is interesting: sector
    and size dominate because they are bridged 49 and 44 times against country's 15.
    """
    facets = gaps["bridged_by_facet"] or {}
    total = sum(facets.values()) or 1
    countries = _hits(scope, COUNTRY_WORDS)
    sectors = _hits(scope, SECTOR_WORDS)
    threats = _hits(scope, THREAT_WORDS)
    quantities = _hits(body, QUANTITY_WORDS)

    our_countries = {c["country"] for c in gaps["cells"]}
    our_sectors = {c["industry"] for c in gaps["cells"]}
    our_threats = {c["threat"] for c in gaps["cells"]}

    score = 0.0
    if set(countries) & our_countries:
        score += 100 * facets.get("country", 0) / total
    if set(sectors) & our_sectors:
        score += 100 * facets.get("sector", 0) / total
    if set(threats) & our_threats:
        score += 100 * facets.get("threat", 0) / total
    # A document that names no measurable quantity cannot move a number whatever it covers.
    if not quantities:
        score = 0.0
    elif "exceedance" in quantities:
        score += 25  # the scarcest thing in the corpus: 7 of 11 maxima declare none_known
    if "loss_magnitude" in quantities:
        score += 10

    return {
        "countries": sorted(set(countries) & our_countries),
        "sectors": sorted(set(sectors) & our_sectors),
        "threats": sorted(set(threats) & our_threats),
        "quantities": sorted(quantities),
        "score": round(score, 1),
    }


def build_intake(root):
    """The candidate register, ranked. Highest promise first."""
    rows = load_intake(root)
    gaps = portfolio_gaps(root)
    out = []
    for row in rows:
        a = dict(row)
        a.setdefault("score", 0)
        out.append(a)
    out.sort(key=lambda r: (-float(r.get("score") or 0), r.get("file", "")))
    return {"candidates": out, "gaps": gaps, "totals": intake_totals(out)}


def intake_totals(rows):
    by_status = {}
    for r in rows:
        by_status[r.get("status", "unassessed")] = by_status.get(r.get("status", "unassessed"), 0) + 1
    scored = [float(r.get("score") or 0) for r in rows]
    return {
        "candidates": len(rows),
        "by_status": by_status,
        "worth_reading": sum(1 for s in scored if s >= 20),
        "parked": sum(1 for s in scored if s < 20),
    }


def intake_defects(root):
    """Ways the register can mislead. Empty is the passing state."""
    root = Path(root)
    raw = root / "sources" / "raw"
    defects = []
    seen = {}
    for row in load_intake(root):
        f = row.get("file")
        if not f:
            defects.append(f"{row.get('id')}: no file")
            continue
        if raw.exists() and list(raw.iterdir()) and not (raw / f).exists():
            defects.append(f"{f}: not in a populated sources/raw/")
        if f in seen:
            defects.append(f"{f}: listed twice")
        seen[f] = True
        if row.get("status") == "admitted" and not row.get("source_id"):
            defects.append(f"{f}: admitted with no source_id to admit it as")
    return sorted(defects)


# --- The join that was missing -------------------------------------------
# The intake register knows what documents are on disk. The source audit knows
# which sources it cannot read. Nothing compared them, and on 2026-08-23 the
# consequence surfaced: the real 9,852-word *Cost of Insider Risks Global Report
# 2023* sat in the register marked `parked`, while the audit row for that exact
# source read `no_readable_artifact` because the gatherer had only ever reached
# its announcement page. Both records were correct. Neither could see the other.
#
# That was the seventh time a source recorded as owed turned out to be held, so
# this is the check rather than another note telling a reader to go and look.

_TITLE_STOPWORDS = frozenset({
    "the", "a", "an", "of", "in", "and", "for", "on", "to",
    "report", "study", "survey", "annual", "edition", "whitepaper", "global",
    "release", "rapport", "barometre",
})
_TITLE_TOKEN = re.compile(r"[a-z0-9]+")


def _title_tokens(title):
    """A title reduced to the words that identify the document, year kept.

    The year is deliberately significant: dropping it made every Sophos country
    cut match every other year of itself, which turns a useful check into noise.
    """
    return {w for w in _TITLE_TOKEN.findall((title or "").lower())
            if w not in _TITLE_STOPWORDS and len(w) > 2}


def blocked_but_held(root):
    """Sources the audit cannot read, for which a candidate document is on disk.

    Conservative on purpose: every identifying token of the registered title,
    the year included, must appear in the candidate's extracted title. A missed
    match costs one more manual look; a false match sends a reader to the wrong
    document and teaches them to ignore the check.
    """
    from engine.source_audit import NO_ARTIFACT, PROPERTIES, load_audit, load_registry

    registry = {s.get("id"): s for s in load_registry(root)}
    candidates = load_intake(root)
    rows = []
    for entry in load_audit(root):
        properties = entry.get("properties") or {}
        if not any((properties.get(p) or {}).get("basis") == NO_ARTIFACT for p in PROPERTIES):
            continue
        source = registry.get(entry.get("source_id")) or {}
        wanted = _title_tokens(source.get("title"))
        if not wanted:
            continue
        for candidate in candidates:
            if candidate.get("status") == "admitted":
                continue
            if wanted <= _title_tokens(candidate.get("title")):
                rows.append({
                    "source_id": entry.get("source_id"),
                    "title": source.get("title"),
                    "file": candidate.get("file"),
                    "words": candidate.get("words"),
                    "status": candidate.get("status"),
                })
    return rows
