#!/usr/bin/env python3
"""Build the public source-audit page from the repo's own audit records.

Roadmap milestone M2. The audit's finding has been public since v0.9.0 and the
evidence for it has not: it lives in `sources/audit.yaml`, a machine file nobody
reads, so a stranger could see the claim and had no way to check it without
cloning the repo. This renders the same records as a page they can link to, cite,
and dispute one row at a time.

Everything here is generated from `engine/source_audit.py`. Nothing is authored in
the template except the framing, which is why the counts on the page cannot drift
from the counts in the doctor.

Two rules the rendering has to keep, because both are easy to lose in a table:

**A count travels with its denominator.** 58 of 72 read is the claim; "58 sources"
is not. The header states every slot count, and a claim drawn from this page is
expected to carry them.

**Unread is not absence, and blocked is not unread.** A source nobody has read yet
is an open question. A source whose stored artifact is a landing page is blocked
until someone obtains the document, and no amount of reading clears it. The three
render differently and are never summed.

Re-run after any audit change: `python scripts/build_audit_page.py`.
"""
import argparse
import html
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source_audit import (  # noqa: E402
    PROPERTIES,
    PROPERTY_QUESTION,
    build_source_audit,
    manifest_hashes,
)

TEMPLATE = Path(__file__).resolve().parent / "audit_template.html"
REPO_URL = "https://github.com/raviaxo/RiskShard"
SITE_URL = "https://raviaxo.github.io/RiskShard/"

VERIFIED = "verified_against_artifact"
BLOCKED = "no_readable_artifact"


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def answer(prop):
    """One property's answer as (label, css class).

    A verified yes and a verified no render at the same weight on purpose. The
    audit is not a scoreboard, and a source that publishes nothing is not failing
    at anything — it is measuring what it says it measures.
    """
    basis = (prop or {}).get("basis")
    if basis == VERIFIED:
        publishes = bool(prop.get("publishes"))
        return ("yes", "a a-yes") if publishes else ("no", "a a-no")
    if basis == BLOCKED:
        return "blocked", "a a-blocked"
    return "unread", "a a-unread"


def dispute_url(source_id, prop_name):
    title = f"Audit answer disputed: {source_id} / {prop_name}"
    return (f"{REPO_URL}/issues/new?title={html.escape(title.replace(' ', '%20'), quote=True)}"
            f"&labels=audit-dispute")


def render_questions(audit):
    """The four questions, each with how many sources answered yes."""
    rows = []
    for prop in PROPERTIES:
        yes = sum(
            1 for s in audit["sources"]
            if (s["properties"].get(prop) or {}).get("basis") == VERIFIED
            and (s["properties"][prop].get("publishes"))
        )
        read = audit["coverage"]["verified_by_property"].get(prop, 0)
        rows.append(
            f'<tr><td class="k">{esc(prop)}</td><td>{esc(PROPERTY_QUESTION[prop])}</td>'
            f'<td class="n"><b>{yes}</b> of {read} read</td></tr>'
        )
    return "\n".join(rows)


def render_matrix(audit):
    rows = []
    for source in audit["sources"]:
        cells = []
        for prop in PROPERTIES:
            label, klass = answer(source["properties"].get(prop))
            cells.append(f'<td class="c"><span class="{klass}">{label}</span></td>')
        rows.append(
            f'<tr><td class="src"><a href="#{esc(source["source_id"])}">'
            f'{esc(source["title"] or source["source_id"])}</a>'
            f'<div class="pub">{esc(source["publisher"] or "")}</div></td>'
            + "".join(cells) + "</tr>"
        )
    return "\n".join(rows)


def render_records(audit, hashes):
    out = []
    for source in audit["sources"]:
        sid = source["source_id"]
        digest = hashes.get(sid)
        meta = [f"<code>{esc(sid)}</code>"]
        if source.get("artifact"):
            meta.append(esc(source["artifact"]))
        if digest:
            # The hash is the citation. A path is only recheckable on the machine
            # that gathered it; sources/raw/ is not distributed.
            meta.append(f"sha256 {esc(digest[:16])}&hellip;")
        props = []
        for prop in PROPERTIES:
            record = source["properties"].get(prop) or {}
            label, klass = answer(record)
            stamp = record.get("verified_on")
            props.append(
                f'<div class="prop">'
                f'<div class="propq">{esc(PROPERTY_QUESTION[prop])}</div>'
                f'<div class="propa"><span class="{klass}">{label}</span></div>'
                f'<div class="detail">{esc(record.get("detail") or "Not yet asked.")}</div>'
                + (f'<div class="stamp">read {esc(stamp)}</div>' if stamp else "")
                + "</div>"
            )
        out.append(
            f'<div class="rec" id="{esc(sid)}">'
            f'<div class="rechead"><h3>{esc(source["title"] or sid)}</h3>'
            f'<span class="pub">{esc(source["publisher"] or "")}</span></div>'
            f'<div class="recmeta">{" &middot; ".join(meta)}</div>'
            + "".join(props)
            + f'<div class="acts"><a href="{dispute_url(sid, "answer")}">[dispute an answer]</a>'
              f'<a href="{REPO_URL}/blob/main/sources/audit.yaml">[the record]</a></div>'
            + "</div>"
        )
    return "\n".join(out)


def render(audit, hashes, repo_url=REPO_URL, site_url=SITE_URL, stamp=""):
    coverage = audit["coverage"]
    fields = {
        "__RS_SOURCES__": str(coverage["sources"]),
        "__RS_FULLY__": f'{coverage["sources_fully_verified"]} of {coverage["sources"]}',
        "__RS_VERIFIED__": str(coverage["verified"]),
        "__RS_SLOTS__": str(coverage["slots"]),
        "__RS_BLOCKED__": str(coverage["blocked_no_artifact"]),
        "__RS_UNREAD__": str(coverage["unverified"]),
        "__RS_QUESTIONS__": render_questions(audit),
        "__RS_MATRIX__": render_matrix(audit),
        "__RS_RECORDS__": render_records(audit, hashes),
        "__RS_REPO__": repo_url,
        "__RS_SITE__": site_url,
        "__RS_STAMP__": stamp or "Public cyber-loss evidence",
    }
    markup = TEMPLATE.read_text(encoding="utf-8")
    for token, value in fields.items():
        markup = markup.replace(token, value)
    return markup


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the public source-audit page.")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "audit.html")
    parser.add_argument("--check", action="store_true",
                        help="render without writing; exit non-zero if a token is left unfilled")
    args = parser.parse_args(argv)

    audit = build_source_audit(ROOT)
    markup = render(audit, manifest_hashes(ROOT))

    if "__RS_" in markup:
        print("Unfilled template token remains — the page was not written.")
        return 1
    if args.check:
        print("Audit page renders clean.")
        return 0

    args.output.write_text(markup, encoding="utf-8")
    coverage = audit["coverage"]
    print(f"Audit page written: {args.output}")
    print(f"  {coverage['sources_fully_verified']} of {coverage['sources']} sources read on all "
          f"four properties · {coverage['verified']} of {coverage['slots']} answers verified")
    print(f"  {coverage['blocked_no_artifact']} blocked · {coverage['unverified']} unread")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
