"""ADR-0015 — what each registered source publishes, and on what basis we say so.

The whole module turns on one distinction. *What we extracted from a source* is
mechanically derivable from `evidence/`. *What a source publishes* is not derivable
from anything in this repository — it requires reading the source. Inferring the
second from the first would produce an audit that is fast, mechanical, checkable and
wrong, and the error would be invisible because the derivation looks rigorous.

So nothing here infers. The corpus view is computed and labelled as a fact about us;
the source view is read from `sources/audit.yaml`, where a claim must carry
`verified_against_artifact` to count. Coverage — how much of the audit is actually
read — is computed and published beside every finding it supports.
"""
import json
from pathlib import Path

import yaml

AUDIT_RELPATH = Path("sources") / "audit.yaml"
REGISTRY_RELPATH = Path("sources") / "registry.yaml"

PROPERTIES = ("mode", "distribution", "exceedance", "population")

PROPERTY_QUESTION = {
    "mode": "Does it publish a most-likely / modal value — the beta-PERT parameter?",
    "distribution": "Does it publish a distribution or quantiles, or only point statistics?",
    "exceedance": "Does it state how often a loss of a given size is exceeded, over a named population?",
    "population": "Can the measured population be named from the source itself?",
}

VERIFIED = "verified_against_artifact"
DERIVED = "derived_from_corpus"
UNVERIFIED = "unverified"
NO_ARTIFACT = "no_readable_artifact"


def load_registry(root):
    """Every registered source, in registry order."""
    data = yaml.safe_load((Path(root) / REGISTRY_RELPATH).read_text(encoding="utf-8")) or {}
    return data.get("sources") or (data if isinstance(data, list) else [])


def load_audit(root):
    """The audit file, or an empty audit when it does not exist yet."""
    path = Path(root) / AUDIT_RELPATH
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("audit") or []


def corpus_view(root):
    """What our own extraction took from each source. A fact about us, not about it.

    Deliberately reports *presence* only. That a source contributed no record with an
    exceedance basis says nothing about whether the source states one — we may never
    have needed it — which is exactly why this is kept apart from the audit's answers
    rather than folded into them.
    """
    view = {}
    for path in sorted((Path(root) / "evidence").glob("*.yaml")):
        records = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("records") or []
        for record in records:
            sid = record.get("source_id")
            if not sid:
                continue
            entry = view.setdefault(sid, {
                "records": 0,
                "measurement_bases": set(),
                "exceedance_bases": set(),
                "named_populations": 0,
            })
            entry["records"] += 1
            if record.get("measurement_basis"):
                entry["measurement_bases"].add(record["measurement_basis"])
            if record.get("exceedance_basis"):
                entry["exceedance_bases"].add(record["exceedance_basis"])
            applicability = record.get("applicability") or {}
            named = [v for field in ("countries", "industries", "company_size_bands")
                     for v in (applicability.get(field) or [])
                     if v not in ("all", "global")]
            if named:
                entry["named_populations"] += 1
    for entry in view.values():
        entry["measurement_bases"] = sorted(entry["measurement_bases"])
        entry["exceedance_bases"] = sorted(entry["exceedance_bases"])
    return view


def build_source_audit(root):
    """The audit joined to the registry: one row per registered source.

    Sources with no audit entry are not omitted — they are the queue, and an audit
    that silently dropped them would report better coverage than it has.
    """
    root = Path(root)
    audited = {row.get("source_id"): row for row in load_audit(root)}
    corpus = corpus_view(root)
    rows = []
    for source in load_registry(root):
        sid = source.get("id")
        entry = audited.get(sid) or {}
        answers = entry.get("properties") or {}
        rows.append({
            "source_id": sid,
            "title": source.get("title"),
            "publisher": source.get("publisher"),
            "artifact": entry.get("artifact"),
            "corpus": corpus.get(sid, {"records": 0, "measurement_bases": [],
                                       "exceedance_bases": [], "named_populations": 0}),
            "properties": {
                prop: dict(answers.get(prop) or {"basis": UNVERIFIED})
                for prop in PROPERTIES
            },
        })
    return {"sources": rows, "coverage": audit_coverage(rows)}


def audit_coverage(rows):
    """How much of the audit has actually been read — ADR-0015 part 3.

    Published beside every finding the audit supports. A reader gets the denominator
    of our confidence before the claim, which is the whole difference between this and
    the audits it is meant to be an alternative to.
    """
    slots = len(rows) * len(PROPERTIES)
    verified = sum(1 for r in rows for p in PROPERTIES
                   if r["properties"][p].get("basis") == VERIFIED)
    # "not read" and "cannot be read" are different states. Reporting them as one
    # number would let a permanent gap — a source we hold only as a landing page —
    # look like a backlog that effort will clear.
    blocked = sum(1 for r in rows for p in PROPERTIES
                  if r["properties"][p].get("basis") == NO_ARTIFACT)
    by_property = {
        p: sum(1 for r in rows if r["properties"][p].get("basis") == VERIFIED)
        for p in PROPERTIES
    }
    fully = sum(1 for r in rows
                if all(r["properties"][p].get("basis") == VERIFIED for p in PROPERTIES))
    return {
        "sources": len(rows),
        "slots": slots,
        "verified": verified,
        "blocked_no_artifact": blocked,
        "unverified": slots - verified - blocked,
        "sources_fully_verified": fully,
        "verified_by_property": by_property,
    }


def publishable_claim(rows, prop):
    """What may honestly be said about a property, with its denominator attached.

    The only function that produces a source-level statement, and it will not produce
    one without the coverage that qualifies it. `positive` counts sources *read* and
    found to publish the property; `negative` counts sources read and found not to.
    Everything unread is reported as unread rather than as absence — the distinction
    finding 1 was missing when it said "no source consulted does".
    """
    read = [r for r in rows if r["properties"][prop].get("basis") == VERIFIED]
    positive = [r for r in read if r["properties"][prop].get("publishes")]
    return {
        "property": prop,
        "question": PROPERTY_QUESTION[prop],
        "sources_total": len(rows),
        "sources_read": len(read),
        "publishes": len(positive),
        "does_not_publish": len(read) - len(positive),
        "unread": len(rows) - len(read),
        "publishing_source_ids": sorted(r["source_id"] for r in positive),
    }


def manifest_hashes(root):
    """source_id -> sha256 of the gathered artifact, from the committed manifest.

    `sources/raw/` is not distributed — the artifacts are large third-party PDFs — so
    the manifest is what a reader outside this machine actually has. Anchoring a
    verification to the hash rather than a local path is what makes it recheckable by
    someone else, and it was a CI failure on a clean checkout that made that obvious.
    """
    path = Path(root) / "sources" / "manifest.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {s.get("id"): s.get("sha256") for s in data.get("sources", []) if s.get("sha256")}


def audit_defects(root):
    """Ways the audit can lie, checked rather than trusted. Empty is the passing state.

    Every one of these is a shape the schema alone cannot forbid: a source that does
    not exist, a verification pinned to no artifact or to the wrong one, or an answer
    that reads as a source-level claim while resting on our own extraction.
    """
    root = Path(root)
    registry_ids = {s.get("id") for s in load_registry(root)}
    hashes = manifest_hashes(root)
    raw = root / "sources" / "raw"
    defects = []
    for row in load_audit(root):
        sid = row.get("source_id")
        if sid not in registry_ids:
            defects.append(f"{sid}: audited but not in sources/registry.yaml")
        answers = row.get("properties") or {}
        verified = [p for p in PROPERTIES
                    if (answers.get(p) or {}).get("basis") == VERIFIED]
        digest = row.get("artifact_sha256")
        if verified and not digest:
            defects.append(
                f"{sid}: {len(verified)} verified answer(s) with no artifact_sha256 — "
                "nobody else can tell which document was read")
        elif digest and sid in hashes and digest != hashes[sid]:
            defects.append(
                f"{sid}: artifact_sha256 does not match sources/manifest.json — the "
                "audited document is not the gathered one (a new edition?)")
        # A local copy is a convenience, not the guarantee: only checked when present.
        local = row.get("artifact")
        if local and raw.exists() and list(raw.iterdir()) and not (raw / Path(local).name).exists():
            defects.append(f"{sid}: artifact {local} is not in a populated sources/raw/")
        for prop in PROPERTIES:
            answer = answers.get(prop) or {}
            if answer.get("basis") != VERIFIED and "publishes" in answer:
                defects.append(
                    f"{sid}/{prop}: asserts what the source publishes on a "
                    f"{answer.get('basis')!r} basis")
    return sorted(defects)


def format_audit_markdown(audit):
    """The matrix, one row per source — for the report and the doctor's eye.

    Coverage first, deliberately: ADR-0015 part 3 puts the denominator of our
    confidence ahead of anything the audit appears to show.
    """
    coverage = audit["coverage"]
    lines = [
        "# Source audit — what each registered source publishes",
        "",
        f"**Coverage: {coverage['verified']} of {coverage['slots']} answers verified against a "
        f"stored artifact** ({coverage['sources_fully_verified']} of {coverage['sources']} sources "
        "read on all four properties). Every unverified slot is a question we have not answered, "
        "not a finding. ADR-0015.",
        "",
        "| Source | Publisher | " + " | ".join(p.capitalize() for p in PROPERTIES) + " | Records held |",
        "| --- | --- | " + " | ".join("---" for _ in PROPERTIES) + " | --- |",
    ]
    for row in audit["sources"]:
        cells = []
        for prop in PROPERTIES:
            answer = row["properties"][prop]
            if answer.get("basis") == VERIFIED:
                cells.append("**yes**" if answer.get("publishes") else "no")
            elif answer.get("basis") == DERIVED:
                cells.append("_(corpus only)_")
            else:
                cells.append("—")
        lines.append(
            f"| `{row['source_id']}` | {row.get('publisher') or '—'} | "
            + " | ".join(cells)
            + f" | {row['corpus']['records']} |"
        )
    lines += ["", "`—` is unread. It is not a claim in either direction."]
    return "\n".join(lines) + "\n"
