"""Generate the restart point instead of writing it by hand.

`docs/internal/NEXT_STEPS.md` opens with a restart point: the block the next
session reads first to learn where the repository stands. Three consecutive
restart points went stale on the same field, and each one recorded that its
predecessor had.

* The 2026-10-22 block said `ddcdd40`, 531 tests, and no release owed until
  2026-10-26. It was four days and two merged PRs out of date when read.
* The 2026-10-27 block said `ea5cab6`, 542 tests, `v0.13.0` current, and the
  2026-11-01 measurement ten days away. It was ten days **past** when read.
* The 2026-11-20 block said `v0.14.0` was still current, the doctor read 18 of
  19, and "the release is owed". All three were false within the hour, because
  the release was cut after the close commit that recorded them.

(The first draft of this list conflated the first two incidents into one and
dated the second by the close that caught it rather than the close that wrote
it. Corrected by reading the file, which is the lesson of the thing being
built.)

The third one diagnosed itself correctly: *this block describes repo state, and
writing it before the last state change guarantees it is wrong. Write it last,
or generate it.* This module is the second option, which is the only one that
does not depend on remembering.

**What it deliberately does not do is pin a progress figure.** This repository
has been bitten twice by a guard asserting a counter's current value
(`flagged_verified == 4`, then `== 26`), where the next real advance arrives as
a build failure and teaches the reader to edit the constant rather than check
the claim. So the test count, the sha and the doctor line are recorded as
measured facts carrying their measurement date, and `restart_point_status`
compares only the two fields that a docs-only close commit cannot move and that
actually went stale in the incidents above: the current release and the data
pack fingerprint.
"""
import json
import re
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BEGIN_MARKER = "<!-- BEGIN GENERATED RESTART POINT"
END_LINE = "<!-- END GENERATED RESTART POINT -->"
NEXT_STEPS_RELPATH = Path("docs/internal/NEXT_STEPS.md")
RESTART_HEADING = "## Restart point"
WRAP_WIDTH = 95

RELEASE_ID_RE = re.compile(r"-(v\d+\.\d+\.\d+)$")


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


def parse_porcelain_paths(lines):
    """Paths out of `git status --porcelain` lines, without trusting the columns.

    `--porcelain` puts the two status characters in columns 1-2, so `line[3:]` is
    the documented way to read the path — and it was wrong here, because `_git`
    strips its stdout and that eats the leading space of an unstaged first line.
    The block then reported "1 uncommitted path(s)" for a tree whose only change
    was the block itself. Found by running the close ritual rather than by a
    test, which is why this is a function with one.
    """
    paths = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        path = parts[1] if len(parts) == 2 else parts[0]
        paths.append(path.split(" -> ")[-1].strip().strip('"'))
    return paths


def git_state(root):
    """Branch, head, parity with the upstream, and what else is lying around."""
    branch = _git(root, ["branch", "--show-current"])
    head = _git(root, ["rev-parse", "HEAD"])
    upstream = _git(root, ["rev-parse", "--abbrev-ref", "@{u}"])
    ahead = behind = None
    if upstream:
        counts = _git(root, ["rev-list", "--left-right", "--count", f"{upstream}...HEAD"])
        parts = counts.split()
        if len(parts) == 2 and all(p.isdigit() for p in parts):
            behind, ahead = int(parts[0]), int(parts[1])
    dirty = [line for line in _git(root, ["status", "--porcelain"]).splitlines() if line.strip()]
    dirty_paths = parse_porcelain_paths(dirty)
    branches = [b for b in _git(root, ["branch", "--format=%(refname:short)"]).splitlines() if b]
    return {
        "branch": branch,
        "head": head,
        "head_short": head[:7],
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "tree_clean": not dirty,
        "dirty_count": len(dirty),
        "dirty_paths": dirty_paths,
        "local_branches": branches,
        "other_local_branches": [b for b in branches if b != branch],
    }


def open_pull_requests(root):
    """Best effort: the open PR count via `gh`, or None when it cannot be asked."""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return len(json.loads(result.stdout or "[]"))
    except Exception:
        return None


def current_release(root):
    """The newest versioned data pack release, read from disk rather than git tags.

    Git tags are the obvious source and the wrong one: a CI checkout fetches
    depth 1 and no tags, so anything that reads them cannot be checked where it
    matters. `data_pack_releases/` is committed and complete.
    """
    release_dir = Path(root) / "data_pack_releases"
    ids = sorted(p.stem for p in release_dir.glob("*.json") if RELEASE_ID_RE.search(p.stem))
    if not ids:
        return {"release_id": None, "release_version": None,
                "pack_fingerprint": None, "archive_present": None}
    release_id = ids[-1]
    payload = {}
    try:
        payload = json.loads((release_dir / f"{release_id}.json").read_text())
    except Exception:
        payload = {}
    fingerprint = payload.get("fingerprint") or ""
    tag = RELEASE_ID_RE.search(release_id)
    return {
        "release_id": release_id,
        # The payload's own `release_version` field holds the whole release id
        # (`2026.11.20-v0.15.0`), not the tag, so the tag is read off the id.
        "release_version": tag.group(1) if tag else release_id,
        "release_pack_fingerprint": fingerprint[:12],
        "archive_present": (Path(root) / "docs" / "r" / release_id / "index.html").is_file(),
    }


def live_pack_fingerprint(root):
    from engine.data_packs import build_data_pack_manifest

    try:
        return (build_data_pack_manifest(Path(root)).get("fingerprint") or "")[:12]
    except Exception:
        return ""


def test_state(root, *, run_tests=False):
    """Count the suite, and run it when asked.

    The close ritual runs the suite anyway, so `run_tests=True` is how the block
    gets a test line nobody typed.
    """
    root = Path(root)
    if not run_tests:
        try:
            tests_dir = str(root / "tests")
            suite = unittest.TestLoader().discover(tests_dir, top_level_dir=tests_dir)
            return {"ran": False, "count": suite.countTestCases(), "passed": None}
        except Exception as exc:
            return {"ran": False, "count": None, "passed": None, "error": str(exc)}
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    output = result.stderr or result.stdout
    match = re.search(r"^Ran (\d+) tests?", output, re.MULTILINE)
    return {
        "ran": True,
        "count": int(match.group(1)) if match else None,
        "passed": result.returncode == 0,
    }


def gate_state(root):
    """Evidence and preflight, the two gates the restart point has always quoted."""
    root = Path(root)
    state = {}
    try:
        from engine.evidence_quality import validate_evidence_quality

        issues = validate_evidence_quality(root / "evidence", root / "sources" / "manifest.json")
        state["evidence_errors"] = sum(1 for i in issues if i["severity"] == "error")
    except Exception:
        state["evidence_errors"] = None
    try:
        from engine.contributor import build_contributor_preflight

        state["preflight_status"] = build_contributor_preflight(root).get("status")
    except Exception:
        state["preflight_status"] = None
    return state


def doctor_state(root):
    """The doctor's own reading, so the count of checks is never hand-written.

    Imported here rather than at module scope: `engine.doctor` imports this
    module for `restart_point_check`, and only one of the two can be eager.
    """
    from engine.doctor import build_doctor_report

    report = build_doctor_report(Path(root))
    checks = report.get("checks", [])
    return {
        "status": report.get("status"),
        "total": len(checks),
        "passing": sum(1 for c in checks if c["status"] == "pass"),
        "not_passing": [f"{c['name']} ({c['status']})" for c in checks if c["status"] != "pass"],
    }


def collect_session_state(root=PROJECT_ROOT, *, run_tests=False, include_doctor=True,
                          include_prs=True, today=None):
    """Measure everything the restart point claims, in one pass."""
    root = Path(root)
    state = {
        "generated_at": (today or date.today()).isoformat(),
        "git": git_state(root),
        "release": current_release(root),
        "pack_fingerprint": live_pack_fingerprint(root),
        "tests": test_state(root, run_tests=run_tests),
        "gates": gate_state(root),
        "open_prs": open_pull_requests(root) if include_prs else None,
        "doctor": doctor_state(root) if include_doctor else None,
    }
    return state


def _sentence_git(git):
    parts = []
    branch = git.get("branch") or "HEAD"
    upstream = git.get("upstream")
    if upstream and git.get("ahead") == 0 and git.get("behind") == 0:
        parts.append(f"`{branch}` == `{upstream}`")
    elif upstream:
        ahead, behind = git.get("ahead"), git.get("behind")
        if ahead is None or behind is None:
            parts.append(f"`{branch}` vs `{upstream}`: divergence unknown")
        else:
            parts.append(f"`{branch}` is {ahead} ahead / {behind} behind `{upstream}`")
    else:
        parts.append(f"`{branch}` has no upstream")
    # The block is written before it is committed, so at close time this file is
    # always among the dirty paths. Saying "1 uncommitted path" there would be true
    # and useless; saying "clean" would be false. It says which.
    others = [path for path in (git.get("dirty_paths") or [])
              if path != NEXT_STEPS_RELPATH.as_posix()]
    if git.get("tree_clean"):
        parts.append("tree clean")
    elif not others:
        parts.append("tree clean but for this file, uncommitted as written")
    else:
        parts.append(f"**{git.get('dirty_count')} uncommitted path(s)**")
    branches = git.get("other_local_branches") or []
    parts.append("no other local branch" if not branches
                 else f"other local branch(es): {', '.join(f'`{b}`' for b in branches)}")
    return "; ".join(parts)


def _sentence_release(release):
    if not release.get("release_id"):
        return "No versioned release on disk."
    archive = ("pinned archive committed" if release.get("archive_present")
               else "**no pinned archive — a pinned citation 404s**")
    return (f"`{release['release_version']}` is the current release "
            f"(`{release['release_id']}`), {archive}.")


def _sentence_tests(tests):
    count = tests.get("count")
    if count is None:
        return "Test count unavailable."
    if not tests.get("ran"):
        return f"{count} tests collected (not run in this measurement)."
    return f"{count} tests pass." if tests.get("passed") else f"**{count} tests ran and the suite failed.**"


def _sentence_gates(gates):
    bits = []
    errors = gates.get("evidence_errors")
    if errors == 0:
        bits.append("evidence clean")
    elif errors is None:
        bits.append("evidence unread")
    else:
        bits.append(f"**evidence {errors} error(s)**")
    status = gates.get("preflight_status")
    if status == "pass":
        bits.append("preflight clean")
    elif status is None:
        bits.append("preflight unread")
    else:
        bits.append(f"**preflight {status}**")
    return ", ".join(bits).capitalize() + "."


def _sentence_doctor(doctor):
    if not doctor:
        return ""
    total, passing = doctor.get("total"), doctor.get("passing")
    if doctor.get("status") == "pass":
        return f"The doctor reads **pass on all {total}**."
    names = "; ".join(doctor.get("not_passing") or [])
    return f"The doctor reads **{passing} of {total}** — {names}."


def recorded_fields(state):
    """The subset a later run can check this block against."""
    return {
        "generated_at": state["generated_at"],
        "head": state["git"].get("head", ""),
        "release_version": state["release"].get("release_version"),
        "pack_fingerprint": state.get("pack_fingerprint"),
    }


def render_restart_point(state):
    """The block, machine-readable header first and prose generated from it."""
    import textwrap

    git = state["git"]
    prose = " ".join(part for part in [
        f"**Repo state, measured {state['generated_at']} at `{git.get('head_short', '?')}`.**",
        _sentence_git(git) + ".",
        (f"No open PR." if state.get("open_prs") == 0
         else f"**{state['open_prs']} open PR(s).**" if state.get("open_prs") else ""),
        _sentence_release(state["release"]),
        _sentence_tests(state["tests"]),
        _sentence_gates(state["gates"]),
        _sentence_doctor(state["doctor"]),
        f"Data pack `{state.get('pack_fingerprint') or '?'}`.",
    ] if part)
    header = json.dumps(recorded_fields(state), sort_keys=True)
    return "\n".join([
        f"{BEGIN_MARKER} — generated by `scripts/session_state.py --write`; do not hand-edit.",
        f"state: {header} -->",
        "",
        textwrap.fill(prose, width=WRAP_WIDTH),
        "",
        END_LINE,
    ]) + "\n"


def parse_restart_point(text):
    """Pull the recorded fields out of a document (or a bare block). None if absent."""
    start = text.find(BEGIN_MARKER)
    if start == -1:
        return None
    match = re.search(r"^state:\s*(\{.*?\})\s*-->\s*$", text[start:], re.MULTILINE | re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def restart_point_status(root=PROJECT_ROOT, *, document=None, live=None):
    """Compare the recorded block against live state on the fields that can drift.

    Only two are compared, and the restraint is the point — see this module's
    docstring. The release and the pack fingerprint are both unmoved by the
    docs-only commit that records them, and both are what went stale when a
    release was cut after the block was written.
    """
    root = Path(root)
    path = root / NEXT_STEPS_RELPATH
    if document is None:
        document = path.read_text() if path.is_file() else ""
    recorded = parse_restart_point(document)
    if live is None:
        release = current_release(root)
        live = {
            "release_version": release.get("release_version"),
            "pack_fingerprint": live_pack_fingerprint(root),
        }
    if recorded is None:
        return {
            "recorded": None,
            "live": live,
            "drift": ["no generated restart point in docs/internal/NEXT_STEPS.md "
                      "- run scripts/session_state.py --write"],
        }
    drift = []
    if recorded.get("release_version") != live.get("release_version"):
        drift.append(
            f"restart point says the current release is "
            f"{recorded.get('release_version')!r}, disk says {live.get('release_version')!r}"
        )
    if recorded.get("pack_fingerprint") != live.get("pack_fingerprint"):
        drift.append(
            f"restart point records data pack {recorded.get('pack_fingerprint')!r}, "
            f"current pack is {live.get('pack_fingerprint')!r}"
        )
    return {"recorded": recorded, "live": live, "drift": drift}


def splice_restart_point(document, block):
    """Replace the generated block, or insert it under the Restart point heading."""
    start = document.find(BEGIN_MARKER)
    if start != -1:
        end = document.find(END_LINE, start)
        if end == -1:
            raise ValueError(f"found {BEGIN_MARKER!r} with no {END_LINE!r} after it")
        end += len(END_LINE)
        tail = document[end:]
        if tail.startswith("\n"):
            tail = tail[1:]
        return document[:start] + block + tail
    heading = document.find(RESTART_HEADING)
    if heading == -1:
        raise ValueError(f"{RESTART_HEADING!r} not found")
    after = document.find("\n", heading)
    if after == -1:
        return document + "\n" + block
    insert = after + 1
    while document[insert:insert + 1] == "\n":
        insert += 1
    return document[:insert] + block + "\n" + document[insert:]


def write_restart_point(root=PROJECT_ROOT, *, state=None, run_tests=False):
    """Generate and splice the block. Returns (path, block).

    Written in two passes, for a reason worth stating. The doctor's `restart
    point` check reads the block in the document, so a doctor reading taken
    *before* the write describes the block being replaced — the first run of
    this function recorded "19 of 20 - restart point (needs_review)" into the
    very block that cleared it. So the first pass writes everything but the
    doctor line, the doctor then reads that block, and the second pass records
    what it said. The two passes record identical release, pack, head and date
    fields, so the second reading holds for the block it lands in.
    """
    root = Path(root)
    path = root / NEXT_STEPS_RELPATH
    if state is None:
        state = collect_session_state(root, run_tests=run_tests, include_doctor=False)
        path.write_text(splice_restart_point(path.read_text(), render_restart_point(state)))
        state["doctor"] = doctor_state(root)
    block = render_restart_point(state)
    path.write_text(splice_restart_point(path.read_text(), block))
    return path, block
