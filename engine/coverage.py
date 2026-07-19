"""Coverage / confidence rubric.

Turns the per-shard signals already computed by the shard registry
(source-backed vs. assumption vs. missing direct parameters, pack confidence,
feed freshness, module maturity) into a single legible **data-strength grade**
plus a plain-language self-qualification line and a contribution funnel.

It invents no new signals and applies no thresholds beyond counting the existing
evidence-pack fields, so a shard's grade is a deterministic function of its
governed evidence. The rubric deliberately tops out at ``source_backed``: whether
a shard may be called benchmark-grade is a human review decision, never a machine
grade. See ``docs/METHODOLOGY.md``.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path

from engine.shard_registry import build_shard_registry


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ordered strongest -> weakest. Each grade is defined purely by counting the
# existing direct-parameter statuses; the "fit" line is the user
# self-qualification ("can I use this number for my decision?").
GRADES = {
    "source_backed": {
        "rank": 0,
        "label": "source-backed",
        "fit": (
            "Suitable for expert practitioner review and internal risk framing. "
            "Not a human-approved benchmark; confirm the shard's caveats before "
            "external or capital/insurance use."
        ),
    },
    "bridged": {
        "rank": 1,
        "label": "assumption-bridged",
        "fit": (
            "Use for directional framing and internal discussion only, not "
            "capital or insurance decisions. Run `packs` to see which parameters "
            "are bridged or estimated."
        ),
    },
    "provisional": {
        "rank": 2,
        "label": "provisional",
        "fit": (
            "Not decision-ready: some parameters have no evidence at all. Use it "
            "to see the workflow, not to quote a number."
        ),
    },
    "scaffold": {
        "rank": 3,
        "label": "scaffold",
        "fit": "Do not use for any decision; this is a contribution scaffold.",
    },
}


def grade_shard(evidence_summary):
    """Grade one shard's data strength from its evidence summary.

    ``evidence_summary`` is the dict the shard registry already builds
    (``source_backed_direct``, ``assumption_only_direct``, ``missing_direct``,
    ``direct_total``, ``pack_confidence``, ``freshness_status``).

    The grade is a function of the governed evidence only. It deliberately does
    NOT read the module ``status`` label (which drifts and is hand-maintained)
    and does NOT claim benchmark status: "cleared the automated gate" is owned by
    ``benchmark_program``, and "benchmark-grade" is a human ledger decision.
    """
    total = evidence_summary.get("direct_total") or 0
    source_backed = evidence_summary.get("source_backed_direct", 0)
    assumptions = evidence_summary.get("assumption_only_direct", 0)
    missing = evidence_summary.get("missing_direct", 0)
    confidence = evidence_summary.get("pack_confidence", "none")
    freshness = evidence_summary.get("freshness_status", "unknown")

    if total == 0 or confidence == "none" or missing >= total:
        grade = "scaffold"
    elif missing > 0:
        grade = "provisional"
    elif source_backed < total:
        grade = "bridged"
    else:
        grade = "source_backed"

    label = GRADES[grade]["label"]
    if grade == "source_backed" and confidence in ("medium", "high"):
        label = f"{label} ({confidence} confidence)"

    flags = []
    if freshness == "needs_source_review":
        flags.append(
            "stale-feeds: at least one source is past its renewal date; refresh "
            "before quoting."
        )

    return {
        "grade": grade,
        "rank": GRADES[grade]["rank"],
        "label": label,
        "fit": GRADES[grade]["fit"],
        "flags": flags,
        "source_backed": source_backed,
        "assumptions": assumptions,
        "missing": missing,
        "total": total,
        "confidence": confidence,
        "freshness": freshness,
    }


def build_coverage_report(root=PROJECT_ROOT, module_id=None):
    registry = build_shard_registry(root)
    entries = registry["entries"]
    if module_id:
        entries = [entry for entry in entries if entry["id"] == module_id]

    graded = []
    for entry in entries:
        grade = grade_shard(entry["evidence_summary"])
        graded.append({
            "id": entry["id"],
            "title": entry["title"],
            "context": entry["context"],
            "threat": entry["threat"],
            "maturity": entry["maturity"],
            "grade": grade,
        })

    graded.sort(key=lambda item: (item["grade"]["rank"], item["id"]))
    grade_counts = Counter(item["grade"]["grade"] for item in graded)

    return {
        "report_type": "riskshard_coverage",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "shard_count": len(graded),
        "grade_counts": {name: grade_counts.get(name, 0) for name in GRADES},
        "shards": graded,
    }


def _context_label(context):
    return "/".join(
        str(context.get(field, "")) for field in ("country", "industry", "company_size")
    )


def format_coverage_report(report):
    lines = [
        "RiskShard coverage & confidence",
        f"Shards: {report['shard_count']}",
        "Grades: " + _format_grade_counts(report["grade_counts"]),
        "",
        "How to read the grade (data strength, not benchmark status):",
        "  source-backed     all 6 parameters trace to reviewed public sources.",
        "  assumption-bridged all present, but some are labeled bridges/estimates.",
        "  provisional       one or more parameters have no evidence yet.",
        "  scaffold          contribution placeholder; do not use the number.",
        "  No grade means benchmark-grade: that is a human decision in the ledger.",
        "  Automated gate status: python scripts/benchmark_program.py --cohort seeded",
        "",
        "Shards (strongest first)",
    ]
    for item in report["shards"]:
        grade = item["grade"]
        lines.append(
            f"- {item['id']}: {grade['label']} "
            f"[{grade['source_backed']}/{grade['total']} source-backed, "
            f"{grade['assumptions']} bridged, {grade['missing']} missing] "
            f"/ {_context_label(item['context'])} / {item['threat']}"
        )
        lines.append(f"    fit: {grade['fit']}")
        for flag in grade["flags"]:
            lines.append(f"    flag: {flag}")

    funnel = [
        item for item in report["shards"]
        if item["grade"]["grade"] in ("bridged", "provisional", "scaffold")
    ]
    lines.extend(["", "Where to contribute (weakest first)"])
    if funnel:
        for item in funnel:
            grade = item["grade"]
            gap = grade["missing"] + grade["assumptions"]
            lines.append(
                f"- {item['id']}: {gap} of {grade['total']} parameters need "
                f"stronger evidence -> python scripts/riskshard_modules.py "
                f"propose {item['id']}"
            )
    else:
        lines.append("- Every shard is fully source-backed; deepen confidence and freshness next.")

    return "\n".join(lines) + "\n"


def _format_grade_counts(counts):
    ordered = sorted(counts.items(), key=lambda kv: GRADES[kv[0]]["rank"])
    parts = [f"{GRADES[name]['label']}={count}" for name, count in ordered if count]
    return ", ".join(parts) or "none"


# Grade -> severity color role for the visual (RAG is severity-only; grade maps to it).
_GRADE_COLOR = {
    "source_backed": "var(--sys)",
    "bridged": "var(--caution)",
    "provisional": "var(--alert)",
    "scaffold": "var(--muted)",
}

_COVERAGE_CSS = """
  :root{--bg:#0b0e14;--panel:#111621;--panel2:#161d2a;--line:#222b3a;--text:#e6edf3;
  --muted:#8794a8;--identity:#7c8cff;--identity-bg:rgba(124,140,255,.10);--data:#38d3e6;
  --sys:#35c98b;--caution:#f2b23e;--alert:#f26d75;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --sans:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;}
  *{box-sizing:border-box;} body{margin:0;background:var(--bg);color:var(--text);
  font-family:var(--sans);font-size:14px;line-height:1.5;padding:32px;max-width:1040px;margin:0 auto;}
  .eyebrow{font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.16em;color:var(--identity);}
  h1{margin:6px 0 4px;font-size:26px;letter-spacing:-.01em;}
  .sub{color:var(--muted);margin:0 0 24px;}
  .tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:28px;}
  .tile{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:14px;}
  .tile .k{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.13em;color:var(--muted);}
  .tile .v{font-family:var(--mono);font-size:26px;font-weight:600;color:var(--data);margin-top:6px;letter-spacing:-.02em;}
  table{width:100%;border-collapse:collapse;margin-bottom:28px;}
  th{text-align:left;font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.12em;
  color:var(--muted);font-weight:600;padding:0 10px 8px;border-bottom:1px solid var(--line);}
  td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:middle;}
  tr:last-child td{border-bottom:0;}
  .id{font-weight:600;} .ctx{color:var(--muted);font-size:12.5px;margin-top:2px;}
  .pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;
  padding:3px 9px;border-radius:999px;border:1px solid var(--line);white-space:nowrap;}
  .dot{width:7px;height:7px;border-radius:999px;}
  .bar{height:7px;border-radius:999px;background:var(--panel2);overflow:hidden;min-width:110px;}
  .bar span{display:block;height:100%;border-radius:999px;}
  .num{font-family:var(--mono);color:var(--data);font-size:12.5px;}
  .help{border:1px solid rgba(124,140,255,.28);background:var(--identity-bg);border-radius:12px;padding:16px 18px;margin-bottom:20px;}
  .help h2{margin:0 0 8px;font-size:15px;} .help ul{margin:8px 0 0;padding-left:18px;color:var(--muted);}
  .help code{font-family:var(--mono);color:var(--identity);font-size:12.5px;}
  footer{color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:14px;}
"""


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_coverage_html(report):
    shards = report["shards"]
    countries = sorted({s["context"].get("country") for s in shards if s["context"].get("country")})
    threats = sorted({s["threat"] for s in shards if s.get("threat")})
    source_backed = sum(1 for s in shards if s["grade"]["grade"] == "source_backed")
    high_conf = sum(
        1 for s in shards
        if s["grade"]["grade"] == "source_backed" and s["grade"]["confidence"] == "high"
    )
    tiles = [
        ("Shards", len(shards)),
        ("Source-backed", source_backed),
        ("High-confidence", high_conf),
        ("Countries", len(countries)),
        ("Threats", len(threats)),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="k">{_esc(k)}</div><div class="v">{v}</div></div>'
        for k, v in tiles
    )

    rows = []
    for s in shards:
        g = s["grade"]
        color = _GRADE_COLOR[g["grade"]]
        pct = int(round(100 * g["source_backed"] / g["total"])) if g["total"] else 0
        ctx = _context_label(s["context"])
        conf = g["confidence"] if g["grade"] == "source_backed" else "—"
        rows.append(
            f'<tr><td><div class="id">{_esc(s["id"])}</div>'
            f'<div class="ctx">{_esc(ctx)} · {_esc(s["threat"])}</div></td>'
            f'<td><span class="pill"><span class="dot" style="background:{color}"></span>'
            f'{_esc(g["label"])}</span></td>'
            f'<td><div style="display:flex;align-items:center;gap:10px">'
            f'<div class="bar"><span style="width:{pct}%;background:{color}"></span></div>'
            f'<span class="num">{g["source_backed"]}/{g["total"]}</span></div></td>'
            f'<td class="num" style="color:var(--muted)">{_esc(conf)}</td></tr>'
        )

    funnel = [s for s in shards if s["grade"]["grade"] in ("bridged", "provisional", "scaffold")]
    help_items = "".join(
        f'<li><strong style="color:var(--text)">{_esc(s["id"])}</strong> — '
        f'{s["grade"]["missing"] + s["grade"]["assumptions"]} of {s["grade"]["total"]} '
        f'parameters need stronger evidence '
        f'(<code>propose {_esc(s["id"])}</code>)</li>'
        for s in funnel
    ) or '<li>Every shard is fully source-backed — deepen confidence and freshness next.</li>'

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RiskShard — Coverage &amp; Confidence</title>
<style>{_COVERAGE_CSS}</style></head><body>
<div class="eyebrow">RiskShard · Evidence coverage</div>
<h1>Coverage &amp; Confidence</h1>
<p class="sub">Every number traces to a reviewed public source. This is the honest
map of what is strong, what is bridged, and where contributions help most.
Generated {_esc(report["generated_at"])}.</p>
<div class="tiles">{tile_html}</div>
<table><thead><tr><th>Shard</th><th>Data strength</th><th>Source-backed</th><th>Confidence</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table>
<div class="help"><h2>Where you can help</h2>
<p style="margin:0;color:var(--muted)">Pick a shard below, bring one reviewed public
source for a weak parameter, and open a pull request. That is how the map fills in.</p>
<ul>{help_items}</ul></div>
<footer>Data strength is not benchmark-grade — calling a shard benchmark-grade is a
recorded human review decision. Reproduce this map:
<code style="font-family:var(--mono);color:var(--identity)">python scripts/coverage_map.py</code></footer>
</body></html>
"""
