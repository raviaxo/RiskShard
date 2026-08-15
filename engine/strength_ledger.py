"""Strength-over-time progress ledger.

Records one source-strength snapshot per data-pack release and computes the
change since the prior release, so "the data got stronger" is a measured delta
rather than an assertion. The strength axis it tracks:

  - params_source_backed : direct parameters that trace to a reviewed source
  - params_bridged       : direct parameters still on labeled bridges/estimates
  - params_missing       : direct parameters with no evidence yet
  - shards_fully_sourced : shards where all 6 direct parameters are source-backed
  - grades               : module maturity-label counts (claim discipline)

ADR-0003 split (recorded since v0.2.0, from the portfolio provenance totals —
the readiness matrix does not carry population data, so these arrive as a
separate input and are absent from pre-split entries):

  - params_cell_matched  : source-backed params whose evidence is drawn from the
                           shard's own population cell
  - params_cross_cell    : source-backed but population-bridged (the public
                           headline calls these "bridged")
  - params_cross_country : the subset of cross-cell bridged on country

ADR-0007 split (recorded since v0.5.0, from the portfolio coherence totals — a
third separate input, for the same reason: neither the readiness matrix nor the
provenance layer measures construct. Absent from pre-split entries):

  - families_coherent    : parameter families whose selected anchors all share
                           one measurement_basis
  - families_mixed       : families composing two or more bases into one range

ADR-0008 split (recorded since v0.6.0, from the portfolio exceedance and
tail-sensitivity layers — the third and last axis, absent from earlier entries):

  - maxima               : impact maxima in the portfolio (the denominator; a
                           maximum is neither quantified nor none_known when it
                           is a legal ceiling, so the two do not sum to it)
  - maxima_quantified    : impact maxima carrying an exceedance statement
                           (modeled_quantile or observed_rank)
  - maxima_none_known    : maxima that declare no exceedance probability at all
  - shards_tail_driven   : shards taking most of their modeled per-event loss
                           from the impact.max anchor alone

An entry is appended only when the data-pack fingerprint changes — i.e. on a
real release. Re-running `record` against an unchanged pack is a no-op, so the
trend cannot be padded with vanity ticks. The ledger JSON is the canonical owner
of the trend (see docs/internal/strength_ledger.json); this module never edits
scenarios, evidence, or any other source of truth.
"""
import json
from pathlib import Path

# The strength metrics summed/counted from the readiness coverage matrix. Kept
# explicit so a delta is always over the same, named set.
METRIC_KEYS = (
    "params_source_backed",
    "params_bridged",
    "params_missing",
    "params_total",
    "shards",
    "shards_fully_sourced",
    "params_cell_matched",
    "params_cross_cell",
    "params_cross_country",
    "families_coherent",
    "families_mixed",
    "maxima",
    "maxima_quantified",
    "maxima_none_known",
    "shards_tail_driven",
    "likely_anchors",
    "likely_not_a_mode",
    "likely_central_tendency",
    "floor_central_tendency",
)

# The ADR-0003 population-split subset of METRIC_KEYS: present only in entries
# recorded with portfolio-provenance totals (v0.2.0 onward).
POPULATION_KEYS = (
    "params_cell_matched",
    "params_cross_cell",
    "params_cross_country",
)

# The ADR-0007 construct-split subset of METRIC_KEYS: present only in entries
# recorded with portfolio-coherence totals (v0.5.0 onward). Same rule as
# POPULATION_KEYS — compute_delta drops a key absent from either side, so the
# first entry carrying these reads "newly measured", never a fabricated delta.
COHERENCE_KEYS = (
    "families_coherent",
    "families_mixed",
)

# The ADR-0008 tail subset of METRIC_KEYS: present only in entries recorded with
# exceedance totals (v0.6.0 onward). Same rule again — the delta drops a key the
# other side never measured, so the first entry reads "newly measured".
TAIL_KEYS = (
    "maxima",
    "maxima_quantified",
    "maxima_none_known",
    "shards_tail_driven",
)

# The anchor-slot subset of METRIC_KEYS: present only in entries recorded with
# slot-role totals (v0.7.0 onward). Same rule a fourth time -- compute_delta drops
# a key absent from either side, so the first entry reads "newly measured" rather
# than inventing an improvement over a release that never measured it.
SLOT_KEYS = (
    "likely_anchors",
    "likely_not_a_mode",
    "likely_central_tendency",
    "floor_central_tendency",
)

LEDGER_RELPATH = Path("docs/internal/strength_ledger.json")


def capture_snapshot(
    dashboard, population_totals=None, coherence_totals=None, tail_totals=None,
    slot_totals=None,
):
    """Reduce a readiness dashboard to the strength snapshot we track over time.

    Returns a dict with the release identity (data-pack version + fingerprint),
    the summed parameter metrics, and the module grade counts. Pure: no I/O.

    `population_totals` is the `totals` dict from
    `engine.provenance.build_portfolio_provenance` — when given, the ADR-0003
    split (cell-matched / cross-cell / cross-country) is recorded alongside the
    matrix metrics. It is a separate input because the readiness matrix does not
    carry population data.

    `coherence_totals` is the `totals` dict from
    `engine.coherence.build_portfolio_coherence` — when given, the ADR-0007
    construct split (coherent / mixed families) is recorded too. Separate for the
    same reason: construct is measured by neither of the other two layers.

    `tail_totals` carries the ADR-0008 axis: `quantified` and `none_known` from
    `engine.exceedance.build_portfolio_exceedance`, plus
    `shards_majority_driven_by_max` from
    `engine.tail_sensitivity.build_portfolio_tail_sensitivity`. Merged by the
    caller because they come from two modules measuring one axis.
    """
    matrix = dashboard.get("evidence_packs", {}).get("coverage_matrix", [])
    source_backed = sum(int(r.get("source_backed_direct", 0)) for r in matrix)
    bridged = sum(int(r.get("assumption_only_direct", 0)) for r in matrix)
    missing = sum(int(r.get("missing_direct", 0)) for r in matrix)
    total = sum(int(r.get("direct_total", 0)) for r in matrix)
    fully_sourced = sum(
        1
        for r in matrix
        if r.get("direct_total") and r.get("source_backed_direct") == r.get("direct_total")
    )
    modules = dashboard.get("risk_modules", {})
    data_pack = dashboard.get("data_pack") or {}
    metrics = {
        "params_source_backed": source_backed,
        "params_bridged": bridged,
        "params_missing": missing,
        "params_total": total,
        "shards": modules.get("module_count", len(matrix)),
        "shards_fully_sourced": fully_sourced,
    }
    if population_totals is not None:
        for key in POPULATION_KEYS:
            metrics[key] = int(population_totals.get(key, 0))
    if coherence_totals is not None:
        # The coherence layer names these `coherent`/`mixed`; the ledger prefixes
        # them so a metric key is never ambiguous about what it counts.
        metrics["families_coherent"] = int(coherence_totals.get("coherent", 0))
        metrics["families_mixed"] = int(coherence_totals.get("mixed", 0))
    if tail_totals is not None:
        metrics["maxima"] = int(tail_totals.get("maxima", 0))
        metrics["maxima_quantified"] = int(tail_totals.get("quantified", 0))
        metrics["maxima_none_known"] = int(tail_totals.get("none_known", 0))
        metrics["shards_tail_driven"] = int(
            tail_totals.get("shards_majority_driven_by_max", 0)
        )
    if slot_totals is not None:
        # The count of likely anchors is recorded explicitly rather than inferred
        # from the categories named beside it. Inferring a denominator from the
        # buckets you happened to list is the bug caught at the v0.6.0 cut.
        metrics["likely_anchors"] = int(slot_totals.get("shards", 0))
        metrics["likely_not_a_mode"] = int(slot_totals.get("mode_slot_declarations", 0))
        metrics["likely_central_tendency"] = int(
            slot_totals.get("shards_mode_slot_central_tendency", 0)
        )
        metrics["floor_central_tendency"] = int(slot_totals.get("shards_floor_slot", 0))
    return {
        "data_pack_version": data_pack.get("pack_version", ""),
        "fingerprint": data_pack.get("fingerprint", ""),
        "metrics": metrics,
        "grades": dict(modules.get("status_counts", {})),
    }


def load_ledger(ledger_path):
    """Load the append-only ledger, or an empty list if it does not exist yet."""
    path = Path(ledger_path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data.get("entries", []) if isinstance(data, dict) else data
    return list(entries)


def save_ledger(ledger_path, entries):
    """Write the ledger back, deterministically (sorted keys, trailing newline)."""
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_comment": (
            "Strength-over-time ledger. One entry per data-pack release; appended "
            "only when the fingerprint changes. Generated by scripts/strength_ledger.py "
            "record — do not hand-edit."
        ),
        "entries": entries,
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def compute_delta(prev_metrics, curr_metrics):
    """Per-metric (current - previous). None if there is no prior entry.

    A key is only included when both entries measured it: pre-split entries
    lack the ADR-0003 population keys, and reporting "+28 cell-matched" against
    an entry that never measured the split would be a fabricated improvement.
    """
    if prev_metrics is None:
        return None
    return {
        k: int(curr_metrics.get(k, 0)) - int(prev_metrics.get(k, 0))
        for k in METRIC_KEYS
        if k in prev_metrics and k in curr_metrics
    }


def build_axis_totals(root):
    """Every declared axis's totals, in one place, for the ledger to record.

    There are two `record_snapshot` call sites — the release cut
    (`scripts/data_pack_manifest.py`) and the standalone recorder
    (`scripts/strength_ledger.py`). Each axis added since v0.2.0 had to be wired into
    both, and at the v0.7.0 cut one of them was missed: the release recorded an entry
    with the fourth axis silently absent. Building the totals here means an axis is
    added once and both callers get it.

    Imported locally so this module keeps its no-heavy-imports property.
    """
    from engine.coherence import build_portfolio_coherence
    from engine.provenance import build_portfolio_provenance
    from engine.slot_roles import build_portfolio_slot_roles
    from engine.tail_sensitivity import build_tail_totals

    return {
        # ADR-0003: the split lives in the provenance layer, not the readiness matrix.
        "population_totals": build_portfolio_provenance(root)["totals"],
        # ADR-0007: construct is measured by the coherence layer only.
        "coherence_totals": build_portfolio_coherence(root)["totals"],
        # ADR-0008: the tail axis spans two modules; build_tail_totals merges them.
        "tail_totals": build_tail_totals(root),
        # The anchor-slot declaration: what role each anchor plays vs. what its slot needs.
        "slot_totals": build_portfolio_slot_roles(root)["totals"],
    }


def record_snapshot(
    ledger_path,
    dashboard,
    date,
    release_version,
    population_totals=None,
    coherence_totals=None,
    tail_totals=None,
    slot_totals=None,
    note=None,
):
    """Append the current snapshot to the ledger — for a named release only.

    `note` is optional prose recorded *with* the entry and rendered beneath the
    public table. It exists because a count on this ledger can move for two very
    different reasons — the evidence changed, or the way we measure it changed —
    and the table cannot tell them apart. v0.8.0 is the case that forced it:
    cell-matched fell 31 → 7 with no parameter, source, value or caveat touched,
    because fit stopped being a hand-maintained field and became a computed one
    (ADR-0013). Under a heading that reads "strength over time", an unexplained
    -24 asserts a collapse that did not happen.

    `release_version` is required and is the enforcement: the rule was documented as
    "on release only" but implemented as "fingerprint differs", and a fingerprint moves
    on any pack edit. Between 2026-07-24 and 2026-07-30 that produced nine entries of
    which one corresponded to an actual release; the rest were noise from a test that
    cut releases into a temp directory and from recording on feature branches. Requiring
    a release version means a bare `record` cannot silently append.

    Still a no-op when the data-pack fingerprint matches the last entry. Returns
    (entry, appended, delta); `delta` is None for the first-ever, baseline, entry.
    """
    if not release_version:
        raise ValueError(
            "record_snapshot requires a release_version: the ledger records releases, "
            "not every pack edit"
        )
    entries = load_ledger(ledger_path)
    snapshot = capture_snapshot(
        dashboard,
        population_totals=population_totals,
        coherence_totals=coherence_totals,
        tail_totals=tail_totals,
        slot_totals=slot_totals,
    )
    prev = entries[-1] if entries else None
    prev_metrics = prev["metrics"] if prev else None

    if prev and prev.get("fingerprint") == snapshot["fingerprint"]:
        # Unchanged pack: no release, no tick. Report the standing delta.
        base = entries[-2]["metrics"] if len(entries) > 1 else None
        return prev, False, compute_delta(base, prev["metrics"])

    entry = {"date": date, "release_version": release_version, **snapshot}
    if note:
        entry["note"] = note
    delta = compute_delta(prev_metrics, snapshot["metrics"])
    entries.append(entry)
    save_ledger(ledger_path, entries)
    return entry, True, delta


def trend(ledger_path):
    """Return every entry paired with its delta vs the prior entry (oldest first).

    Read-only. Each item is (entry, delta_or_None) — the first entry's delta is
    None (baseline). Powers the full-history view.
    """
    entries = load_ledger(ledger_path)
    out = []
    prev_metrics = None
    for entry in entries:
        out.append((entry, compute_delta(prev_metrics, entry["metrics"])))
        prev_metrics = entry["metrics"]
    return out


def latest_delta(ledger_path):
    """Read-only view for consumers (e.g. the weekly digest).

    Returns (latest_entry, delta_vs_prior). Both None if the ledger is empty;
    delta is None when only the baseline entry exists.
    """
    entries = load_ledger(ledger_path)
    if not entries:
        return None, None
    latest = entries[-1]
    prev_metrics = entries[-2]["metrics"] if len(entries) > 1 else None
    return latest, compute_delta(prev_metrics, latest["metrics"])


README_MARKER_BEGIN = "<!-- strength-ledger:begin"
README_MARKER_END = "<!-- strength-ledger:end -->"


def update_readme_progress(readme_path, ledger_path):
    """Rewrite the strength table between the README's ledger markers in place.

    Returns True if the file changed. Raises ValueError if the markers are absent,
    so a silent no-op can never masquerade as an update.
    """
    readme_path = Path(readme_path)
    text = readme_path.read_text(encoding="utf-8")
    begin = text.find(README_MARKER_BEGIN)
    end = text.find(README_MARKER_END)
    if begin == -1 or end == -1 or end < begin:
        raise ValueError("README strength-ledger markers not found or out of order")
    begin_line_end = text.find("\n", begin)
    table = format_progress_markdown(ledger_path).rstrip("\n")
    new_text = text[: begin_line_end + 1] + table + "\n" + text[end:]
    if new_text != text:
        readme_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def baseline_delta(ledger_path):
    """Cumulative change from the first recorded entry to the latest.

    Returns (baseline_entry, delta) or (None, None) when fewer than two entries
    exist — the "since we started measuring" number for the digest.
    """
    entries = load_ledger(ledger_path)
    if len(entries) < 2:
        return None, None
    first, last = entries[0], entries[-1]
    return first, compute_delta(first["metrics"], last["metrics"])


def _signed(n):
    return f"+{n}" if n > 0 else str(n)


def format_progress_markdown(ledger_path):
    """A compact Markdown table of the strength trend, newest first — for the
    public README's Progress section. Returns a stable placeholder when empty.

    Entries carrying a `note` render it beneath the table, marked against the
    release it belongs to. A number that moved because the *measurement* changed
    rather than the evidence must say so where the number is read, not only in a
    changelog the reader of this table has not opened.
    """
    entries = load_ledger(ledger_path)
    if not entries:
        return "_No releases recorded yet._\n"
    rows = trend(ledger_path)
    lines = [
        "| Release | Date | Source-backed params | Cell-matched | Shards 6/6 | Bridged/est. |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry, delta in reversed(rows):
        m = entry["metrics"]

        def cell(key, total_key=None):
            if key not in m:
                return "—"  # entry predates this metric (e.g. the ADR-0003 split)
            base = f"{m[key]}"
            if total_key:
                base += f" / {m[total_key]}"
            if delta and delta.get(key):
                base += f" ({_signed(delta[key])})"
            return base

        lines.append(
            f"| {entry.get('data_pack_version', '?')} | {entry.get('date', '?')} | "
            f"{cell('params_source_backed', 'params_total')} | "
            f"{cell('params_cell_matched')} | "
            f"{cell('shards_fully_sourced', 'shards')} | "
            f"{cell('params_bridged')} |"
        )
    # Labelled by release_version, not the table's Release column: `data_pack_version`
    # repeats (two entries read 2026.07.24), so it cannot identify which row a note
    # belongs to. Entries predating the release-version rule fall back to the pack
    # version plus the date, which separates them.
    for entry, _ in reversed(rows):
        note = entry.get("note")
        if not note:
            continue
        label = entry.get("release_version") or (
            f"{entry.get('data_pack_version', '?')} ({entry.get('date', '?')})"
        )
        lines += ["", f"**{label} —** {note}"]
    return "\n".join(lines) + "\n"
