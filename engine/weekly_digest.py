"""Generate a "Shard Notes" weekly digest skeleton (read-only).

Pulls current project state from the readiness dashboard and recent activity from
git, and formats a Shard Notes template. The auto fields (state, shipped,
contributors) are filled from the repo; the human fills the Lesson and Next lines.
This module changes nothing.
"""
import re
import subprocess
from pathlib import Path

from engine.readiness import build_readiness_dashboard
from engine.strength_ledger import LEDGER_RELPATH, baseline_delta, latest_delta

FILL = "<fill>"


def _git(root, args):
    """Run a read-only git command, returning stdout or "" on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _summarize_state(dashboard):
    modules = dashboard.get("risk_modules", {})
    top_risks = dashboard.get("top_risks", [])
    countries = [
        c
        for c in dashboard.get("localization", {}).get("covered_countries", [])
        if c != "all"
    ]
    matrix = dashboard.get("evidence_packs", {}).get("coverage_matrix", [])
    fully_sourced = sum(
        1
        for row in matrix
        if row.get("source_backed_direct") == row.get("direct_total")
    )
    runnable = [
        r for r in top_risks if str(r.get("status", "")).startswith("calibrated")
    ]
    return {
        "shards": modules.get("module_count", len(matrix)),
        "shards_fully_sourced": fully_sourced,
        "countries": len(countries),
        "top_risks_total": len(top_risks),
        "top_risks_runnable": len(runnable),
        "data_pack_fingerprint": (dashboard.get("data_pack") or {}).get("fingerprint", ""),
    }


def _parse_shipped(root, since_days):
    raw = _git(root, ["log", "--first-parent", f"--since={since_days} days ago", "--pretty=%s"])
    shipped = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Merge pull request"):
            parts = line.split()
            pr = next((p for p in parts if p.startswith("#")), "")
            tail = parts[-1]
            branch = tail.split("/", 1)[-1] if "/" in tail else tail
            shipped.append(f"{pr} {branch}".strip())
        else:
            shipped.append(line)
    return shipped


def _parse_contributors(root, since_days):
    raw = _git(root, ["shortlog", "-sn", "--no-merges", f"--since={since_days} days ago", "HEAD"])
    names = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t") if "\t" in line else line.split(None, 1)
        name = parts[-1].strip()
        if name.endswith("[bot]"):  # skip automation accounts (e.g. dependabot[bot])
            continue
        names.append(name)
    return names


def _strength(root):
    """Read the strength ledger's latest entry + deltas (read-only). None if empty.

    `delta` is the change vs the prior release; `since_baseline` is the cumulative
    change from the first recorded entry (both None until enough history exists).
    """
    path = root / LEDGER_RELPATH
    latest, delta = latest_delta(path)
    if latest is None:
        return None
    base_entry, base_change = baseline_delta(path)
    return {
        "metrics": latest["metrics"],
        "delta": delta,
        "note": latest.get("note"),
        "since_baseline": base_change,
        "baseline_version": base_entry.get("data_pack_version") if base_entry else None,
    }


def build_weekly_digest(root, since_days=7, dashboard=None):
    root = Path(root)
    dashboard = dashboard if dashboard is not None else build_readiness_dashboard(root)
    return {
        "since_days": since_days,
        "state": _summarize_state(dashboard),
        "strength": _strength(root),
        "shipped": _parse_shipped(root, since_days),
        "contributors": _parse_contributors(root, since_days),
    }


def _signed(n):
    return f"+{n}" if n > 0 else str(n)


def _plain(text):
    """Flatten a Markdown ledger note for a plain-text digest.

    The note is authored for the README's Progress table, so it carries emphasis and
    links. This surface is pasted into posts and mail where `**7**` and a relative
    `[finding 6](docs/FINDINGS.md)` both read as noise — the link target is not even
    resolvable away from the repo. Emphasis is dropped and a link becomes its text.
    """
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return " ".join(text.split())


def _format_strength(strength):
    """Render the strength-over-time block: current values, with the release delta
    shown as `prev -> curr (+/-d)` when there is a prior release to compare.

    A release's ledger note is rendered with it. This is the only surface that goes
    *out* rather than waiting to be visited, so it is the worst place for a number to
    move without its reason: v0.8.0 would otherwise have sent `cell-matched: 31 -> 7
    (-24)` to a reader with no way to learn that not one parameter, source, value or
    caveat had changed (ADR-0013, finding 6).
    """
    m = strength["metrics"]
    delta = strength["delta"]
    lines = ["Strength (vs last release):"]
    rows = [
        ("source-backed params", "params_source_backed"),
        ("shards 6/6", "shards_fully_sourced"),
        ("bridged / estimated", "params_bridged"),
    ]
    if "params_cell_matched" in m:
        # ADR-0003 split — only entries recorded since v0.2.0 carry it.
        rows.append(("cell-matched", "params_cell_matched"))
        rows.append(("population-bridged", "params_cross_cell"))
    if delta is None:
        lines[0] = "Strength (baseline):"
        for label, key in rows:
            lines.append(f"  {label}: {m[key]}")
    else:
        for label, key in rows:
            if key not in delta:
                # The prior release predates this metric — no honest arrow to draw.
                lines.append(f"  {label}: {m[key]} (newly measured)")
                continue
            d = delta[key]
            prev = m[key] - d
            tail = f" ({_signed(d)})" if d else " (no change)"
            lines.append(f"  {label}: {prev} -> {m[key]}{tail}")
    note = strength.get("note")
    if note:
        lines.append(f"  why: {_plain(note)}")
    since = strength.get("since_baseline")
    if since is not None:
        base_v = strength.get("baseline_version") or "baseline"
        sp = since["params_source_backed"]
        sb = since["params_bridged"]
        lines.append(
            f"  since {base_v}: {_signed(sp)} source-backed params, "
            f"{_signed(sb)} bridged"
        )
    return lines


def format_weekly_digest(digest, week_of=None, owner_name=None):
    s = digest["state"]
    lines = []

    header = "\U0001f9ea Shard Notes"
    if week_of:
        header += f" — Week of {week_of}"
    lines.append(header)
    lines.append("")

    lines.append(
        f"State: {s['shards']} shards "
        f"({s['shards_fully_sourced']} fully source-backed) · "
        f"{s['countries']} countries · "
        f"{s['top_risks_runnable']}/{s['top_risks_total']} top risks runnable"
    )

    strength = digest.get("strength")
    if strength:
        lines.extend(_format_strength(strength))

    shipped = digest.get("shipped") or []
    if shipped:
        lines.append("Shipped:")
        for item in shipped[:6]:
            lines.append(f"  - {item}")
    else:
        lines.append("Shipped: quiet week — heads-down.")

    contributors = digest.get("contributors") or []
    others = [c for c in contributors if not owner_name or c != owner_name]
    if others:
        lines.append("From the community: " + ", ".join(others))
    else:
        lines.append("From the community: no external contributions yet — issues are open \U0001f447")

    lines.append(f"Lesson: {FILL} — one honest thing you learned this week")
    lines.append(f"Next: {FILL} — the one current objective (see docs/internal/NEXT_STEPS.md)")
    lines.append(
        "Poke holes / bring scenarios: <repo or Discussions link>. "
        "What risk would you want in dollars?"
    )
    return "\n".join(lines) + "\n"
