"""Generate a "Shard Notes" weekly digest skeleton (read-only).

Pulls current project state from the readiness dashboard and recent activity from
git, and formats a Shard Notes template. The auto fields (state, shipped,
contributors) are filled from the repo; the human fills the Lesson and Next lines.
This module changes nothing.
"""
import subprocess
from pathlib import Path

from engine.readiness import build_readiness_dashboard

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


def build_weekly_digest(root, since_days=7, dashboard=None):
    root = Path(root)
    dashboard = dashboard if dashboard is not None else build_readiness_dashboard(root)
    return {
        "since_days": since_days,
        "state": _summarize_state(dashboard),
        "shipped": _parse_shipped(root, since_days),
        "contributors": _parse_contributors(root, since_days),
    }


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
