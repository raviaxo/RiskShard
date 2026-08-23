"""Executive one-page report generator.

Turns a completed simulation run plus a Risk Shard's module descriptor and
evidence pack into a board-facing Markdown summary. It reads only real
structured fields (run stats, module context/notes, evidence-pack trust
metadata); it never invents numbers or caveats.
"""

import html as _html
import re as _re

from engine.composition import compose_module
from engine.fair_calc import IMPACT_UNCERTAINTY_NOTE

DECISION_OPTIONS = (
    ("Accept", "the modeled range is within appetite; monitor and revisit."),
    ("Mitigate", "fund controls to reduce frequency or impact, then re-run."),
    (
        "Gather evidence",
        "commission stronger local claims-severity data before relying on this "
        "for capital or insurance decisions.",
    ),
    (
        "Localize",
        "refine the scenario to our specific size, data sensitivity, and control "
        "posture.",
    ),
)


def _format_amount(value, currency):
    rounded = f"{round(value):,}"
    if currency:
        return f"{currency} {rounded}"
    return rounded


def _humanize(identifier):
    return str(identifier or "").replace("_", " ").strip()


def build_executive_report(run, module, pack, root=None):
    """Assemble structured executive-report fields from real run/module/pack data.

    When ``root`` is supplied, absolute repository paths are stripped from the
    reproduction command so the artifact is safe to share externally.
    """
    portfolio = run["portfolio"]
    metadata = run["metadata"]
    currency_meta = metadata.get("currencies", {})
    currency = currency_meta.get("portfolio_currency")
    reproducibility = metadata.get("reproducibility", {})
    scenarios = reproducibility.get("scenarios", [])
    scenario_meta = scenarios[0] if scenarios else {}

    reproduction_command = reproducibility.get("reproduction_command")
    if reproduction_command and root is not None:
        reproduction_command = reproduction_command.replace(f"{str(root).rstrip('/')}/", "")

    context = module.get("context", {}) if module else {}
    notes = module.get("practitioner_notes", {}) if module else {}
    direct_parameters = pack.get("direct_parameters", []) if pack else []
    source_backed = sum(1 for p in direct_parameters if p.get("status") == "source_backed")

    # Structural methodology caveat first: it governs how the P95/P99 tail above
    # should be read, before any data-specific caveat.
    caveats = [IMPACT_UNCERTAINTY_NOTE]
    status = (pack.get("status") if pack else None) or (module.get("status") if module else None)
    if status and status != "benchmark_grade":
        caveats.append(
            "This is a benchmark "
            f"{_humanize(status).replace('benchmark ', '')} shard, not a "
            "human-approved benchmark: it has cleared automated checks but not "
            "methodology review."
        )
    assumption_count = len(direct_parameters) - source_backed
    if assumption_count > 0:
        caveats.append(
            f"{assumption_count} of {len(direct_parameters)} model parameters rely "
            "on labeled assumptions rather than sources."
        )
    not_good_for = notes.get("not_good_for")
    if not_good_for:
        caveats.append(not_good_for.rstrip("."))
    if currency_meta.get("mixed_or_unspecified"):
        caveats.append(
            "Portfolio totals mix or omit currencies; treat figures as a "
            "smoke-test sum, not a financial decision."
        )

    return {
        "composition": _composition(root, module),
        "title": (module.get("title") if module else None) or scenario_meta.get("name") or "Risk Shard",
        "module_id": module.get("id") if module else scenario_meta.get("name"),
        "threat": (module.get("threat") if module else None) or context.get("threat"),
        "context": context,
        "description": (module.get("description") or "").strip() if module else "",
        "good_for": notes.get("good_for"),
        "currency": currency,
        "mean": portfolio["mean"],
        "p50": portfolio["p50"],
        "p95": portfolio["p95"],
        "p99": portfolio["p99"],
        "pack_confidence": pack.get("pack_confidence") if pack else None,
        "freshness": pack.get("freshness_status") if pack else None,
        "source_backed": source_backed,
        "parameter_total": len(direct_parameters),
        "sources": pack.get("sources", []) if pack else [],
        "caveats": caveats,
        "trials": metadata.get("trials"),
        "distribution": metadata.get("distribution"),
        "base_seed": reproducibility.get("base_seed"),
        "reproduction_command": reproduction_command,
        "fingerprint": scenario_meta.get("fingerprint"),
    }


def _composition(root, module):
    """What the figure rests on, weighted — or an explicit None when it cannot be told.

    "N of M parameters are backed by public sources" reads to a board as a completeness
    score, and for every shard in this portfolio it reads 6 of 6. It says nothing about
    whether any of those sources measured the population the board is asking about, and
    for eight of eleven shards the honest answer is none of them
    ([finding 10](../docs/FINDINGS.md)).

    Returns None rather than raising when the shard cannot be resolved — a report is
    still worth producing without this — and the formatter says so on the page instead
    of quietly dropping the section. A disclosure that degrades to silence is the
    failure mode this whole line of work exists to fix.
    """
    module_id = (module or {}).get("id")
    if not root or not module_id:
        return None
    try:
        return compose_module(root, module_id)
    except (KeyError, ValueError, OSError):
        return None


def _composition_lines(report):
    """The trust section's composition paragraph, per family and never blended."""
    composed = report.get("composition")
    if not composed:
        return ["*What this figure rests on could not be computed for this shard, so it "
                "is not stated. Do not read its absence as nothing to state.*"]
    families = composed.get("families") or {}
    if not {"frequency", "impact"} <= set(families):
        return ["*What this figure rests on is incomplete for this shard and is "
                "therefore not summarised.*"]
    lines = [
        "**What the figure rests on.** A modeled annual loss is a frequency mean times "
        "an impact mean, and the two are anchored differently — so this is stated per "
        "family and never blended into one percentage.",
        "",
    ]
    for name in ("frequency", "impact"):
        data = families[name]
        measured = round(data["measured_share"] * 100)
        elsewhere = round(sum(a["share"] for a in data["anchors"] if a["elsewhere_on"]) * 100)
        dominant = data["dominant"]
        slot = str(dominant["parameter"]).split(".")[-1]
        share = round(dominant["share"] * 100)
        detail = f"**{measured}% measured on this exact context**"
        if elsewhere:
            detail += f", and {elsewhere}% measured on a different one"
        lines.append(f"- **{name.title()}** — {detail}. Most of it ({share}%) comes from "
                     f"the `{slot}` anchor alone.")
    lines.append("")
    lines.append("The annual figure is the product of both means, so it inherits the "
                 "weaker side. *\"Backed by public sources\" above says the evidence is "
                 "published; this says who it was measured on.*")
    return lines


def format_executive_report_markdown(report):
    currency = report["currency"]
    ctx = report["context"]
    context_line = " ".join(
        part for part in [
            _humanize(ctx.get("country")),
            _humanize(ctx.get("industry")),
            _humanize(ctx.get("company_size")),
        ] if part
    )
    threat = _humanize(report["threat"]) or "cyber event"
    mean = _format_amount(report["mean"], currency)
    p95 = _format_amount(report["p95"], currency)
    p99 = _format_amount(report["p99"], currency)

    lines = []
    lines.append(f"# Executive Risk Summary — {report['title']}")
    lines.append("")
    subtitle = f"**Context: {context_line or 'unspecified'} · Threat: {threat}"
    if currency:
        subtitle += f" · Currency: {currency}"
    subtitle += "**"
    lines.append(subtitle)
    lines.append("")

    lines.append("## Bottom line")
    lines.append("")
    lines.append(
        f"A {threat} in this context is modeled to cost an average of **{mean} "
        f"per year**, with a **1-in-20 (P95) year reaching {p95}** and a "
        f"**1-in-100 (P99) year reaching {p99}**. This is a modeled range built "
        "from public evidence, not a prediction of a specific event."
    )
    lines.append("")
    unit = f"Modeled annual loss ({currency})" if currency else "Modeled annual loss"
    lines.append(f"| Metric | {unit} | Plain meaning |")
    lines.append("| --- | ---: | --- |")
    lines.append(f"| Expected (average) | {mean} | Typical year |")
    lines.append(f"| P95 | {p95} | Bad year (1 in 20) |")
    lines.append(f"| P99 | {p99} | Severe year (1 in 100) |")
    lines.append("")

    lines.append("## Why this applies")
    lines.append("")
    why = f"The scenario is matched to **{context_line or 'the supplied context'}**"
    if report["threat"]:
        why += f" and the threat is **{threat}**."
    else:
        why += "."
    lines.append(why)
    if report["description"]:
        lines.append("")
        lines.append(report["description"])
    lines.append("")

    lines.append("## How much to trust it")
    lines.append("")
    confidence = (report["pack_confidence"] or "unrated").upper()
    trust = (
        f"**Confidence: {confidence}.** "
        f"{report['source_backed']} of {report['parameter_total']} model parameters "
        "are backed by public sources"
    )
    if report["freshness"]:
        trust += f", and the underlying feeds are {report['freshness']}."
    else:
        trust += "."
    lines.append(trust)
    lines.append("")
    lines.extend(_composition_lines(report))
    if report["sources"]:
        lines.append("")
        for source in report["sources"]:
            title = source.get("title") or source.get("id")
            tier = source.get("trust_tier")
            published = source.get("publication_date")
            detail = []
            if tier:
                detail.append(f"trust: {tier}")
            if published:
                detail.append(f"published {published}")
            suffix = f" *({'; '.join(detail)})*" if detail else ""
            lines.append(f"- {title}{suffix}")
    lines.append("")

    lines.append("## Key caveats (read before deciding)")
    lines.append("")
    if report["caveats"]:
        for caveat in report["caveats"]:
            lines.append(f"- {caveat}")
    else:
        lines.append("- No structural caveats recorded for this shard.")
    lines.append("")

    lines.append("## Decision the board is being asked to support")
    lines.append("")
    lines.append("Choose one posture for this risk:")
    lines.append("")
    for label, meaning in DECISION_OPTIONS:
        lines.append(f"- **{label}** — {meaning}")
    lines.append("")

    lines.append("---")
    footer = "*Generated by RiskShard"
    if report["module_id"]:
        footer += f" from shard `{report['module_id']}`"
    repro_bits = []
    if report["base_seed"] is not None:
        repro_bits.append(f"seed {report['base_seed']}")
    if report["trials"]:
        repro_bits.append(f"{report['trials']:,} trials")
    if repro_bits:
        footer += f" ({', '.join(repro_bits)})"
    footer += ". "
    if report["reproduction_command"]:
        footer += f"Reproduce: `{report['reproduction_command']}`. "
    footer += "RiskShard outputs are decision support, not assurance.*"
    lines.append(footer)
    lines.append("")

    return "\n".join(lines)


# --- HTML rendering -------------------------------------------------------
# The report has one content source: format_executive_report_markdown. This
# converts that output rather than re-authoring it, so a published page and a
# console-generated .md cannot say different things — the failure this project
# has already had twice, once in a template and once in a README banner.
#
# It handles exactly the constructs the report emits (headings, bold, italic,
# code, bullets, aligned tables, one rule) and nothing else. That is deliberate:
# a general Markdown parser would be a dependency and a surface, and this is
# tested against the actual documents it renders rather than against a spec.

_INLINE = (
    (_re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (_re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"), r"<i>\1</i>"),
    (_re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
)


def _inline(text):
    out = _html.escape(text)
    for pattern, repl in _INLINE:
        out = pattern.sub(repl, out)
    return out


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _alignments(separator):
    out = []
    for cell in _cells(separator):
        if cell.endswith(":") and cell.startswith(":"):
            out.append(' style="text-align:center"')
        elif cell.endswith(":"):
            out.append(' style="text-align:right"')
        else:
            out.append("")
    return out


def _is_separator(line):
    cells = _cells(line)
    return bool(cells) and all(_re.fullmatch(r":?-{3,}:?", c) for c in cells)


def format_executive_report_html(report):
    """The same report as a page body, converted from its own Markdown."""
    lines = format_executive_report_markdown(report).split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
        elif stripped == "---":
            out.append("<hr>")
            i += 1
        elif stripped.startswith("## "):
            out.append(f"<h2>{_inline(stripped[3:])}</h2>")
            i += 1
        elif stripped.startswith("# "):
            out.append(f"<h1>{_inline(stripped[2:])}</h1>")
            i += 1
        elif stripped.startswith("|") and i + 1 < len(lines) and _is_separator(lines[i + 1]):
            head, align = _cells(stripped), _alignments(lines[i + 1])
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            th = "".join(f"<th{align[n] if n < len(align) else ''}>{_inline(c)}</th>"
                         for n, c in enumerate(head))
            body = "".join(
                "<tr>" + "".join(f"<td{align[n] if n < len(align) else ''}>{_inline(c)}</td>"
                                 for n, c in enumerate(r)) + "</tr>" for r in rows)
            out.append(f'<div class="tblwrap"><table><thead><tr>{th}</tr></thead>'
                       f"<tbody>{body}</tbody></table></div>")
        elif stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{_inline(lines[i].strip()[2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
            i += 1
    return "\n".join(out)
