"""Mutation probe: does a guard actually fail when the thing it checks is wrong?

Adopted 2026-11-25. Three guards in three days read stronger than they were, and
**mutation found all three while review found none**:

- A guard searching two concatenated fields was toothless (2026-11-20): stripping the
  base from one field still passed, because the other carried it.
- `parse_porcelain_paths` had 28 tests and none had ever seen git's output
  (2026-11-22) — all written against a hand-built state dict.
- The README measurement-date check (2026-11-22) passed a mutated date, because the
  generated strength-ledger table further down the same file carries a matching one.

The rule those three bought is narrow and lives in `AGENTS.md`: *a test that reads a
document or parses an external tool's output is not done until one mutation of the
thing it checks makes it fail.* This module is that rule taken as built rather than
remembered, because a rule typed into prose has nothing watching it — which is the
same lesson, one level up, as the restart point that had to be generated.

**Why one occurrence and not all of them.** This is the whole design, and it comes
straight out of the IBM case. That guard was `assertIn(date, README.read_text())`, and
the date appears twice in the README: once in the claim, once in a generated table
below it. Mutating *every* occurrence would have made the toothless guard fail —
because then no copy of the date remains — and the probe would have reported teeth it
did not have. Only mutating the claim's own copy exposes it. So a mutation here
touches exactly one occurrence, and a target string that appears more than once is
**refused as ambiguous** until the caller names which one. The trap that hid the
defect becomes a loud error instead of a false pass.

**Why a subprocess.** These guards typically read their document at import or in
`setUpClass`. Mutating the file inside the running interpreter would be invisible to a
document already in memory, so the test runs in a fresh process or the probe proves
nothing.

**What this does not cover, stated rather than discovered.** It probes the
*document-reading* arm of the rule. It cannot catch the `parse_porcelain_paths` defect,
whose fault was that no test had ever seen the real tool's output at all — there was
nothing to mutate, and a probe against a hand-built fixture would have passed happily.
That arm of the rule needs a test that runs the real tool once, and no mutation run
substitutes for it.
"""
import subprocess
import sys
from pathlib import Path

CAUGHT = "caught"
UNCAUGHT = "uncaught"
AMBIGUOUS = "ambiguous"
ABSENT = "absent"

HAS_TEETH = "has_teeth"
TOOTHLESS = "toothless"
BASELINE_RED = "baseline_red"
SELECTOR_UNRESOLVED = "selector_unresolved"
INCONCLUSIVE = "inconclusive"


def run_test(root, selector, python=None):
    """Run one unittest selector in a fresh process. Returns (passed, output)."""
    proc = subprocess.run(
        [python or sys.executable, "-m", "unittest", "-q", selector],
        cwd=str(root), capture_output=True, text=True,
    )
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def _nth_replace(text, old, new, occurrence):
    """Replace only the `occurrence`-th (1-based) instance of `old`."""
    cut = -1
    for _ in range(occurrence):
        cut = text.find(old, cut + 1)
        if cut < 0:
            return None
    return text[:cut] + new + text[cut + len(old):]


def probe(root, selector, mutations, python=None):
    """Probe one guard against a list of mutations.

    `mutations` is a sequence of mappings with `path`, `old`, `new` and an optional
    1-based `occurrence`. Each is applied on its own, against the pristine file, and
    the target is restored byte-for-byte before the next one — including when the test
    run raises.

    A mutation whose target string is absent, or present more than once without an
    explicit `occurrence`, is reported rather than guessed at. Both are findings about
    the guard, not about this tool.
    """
    root = Path(root)
    baseline_pass, baseline_out = run_test(root, selector, python)
    report = {
        "test": selector,
        "baseline": "pass" if baseline_pass else "fail",
        "mutations": [],
        "restored": True,
    }
    if not baseline_pass:
        # unittest reports an unimportable or misspelled selector as a *failing test*
        # (`unittest.loader._FailedTest`), which reads identically to a genuinely red
        # guard. Caught while using this tool on its first real target: a mistyped
        # class name reported BASELINE_RED and sent the author looking for a
        # regression that did not exist.
        if "_FailedTest" in baseline_out:
            report["verdict"] = SELECTOR_UNRESOLVED
            report["detail"] = (
                "the selector does not name a test that could be loaded — check the "
                "module, class and method names before reading this as a red guard"
            )
        else:
            report["verdict"] = BASELINE_RED
            report["detail"] = (
                "the guard does not pass before any mutation, so nothing can be "
                "learned about what makes it fail"
            )
        report["baseline_output"] = baseline_out.strip()[-2000:]
        return report

    for spec in mutations:
        target = root / spec["path"]
        old, new = spec["old"], spec["new"]
        original = target.read_bytes()
        text = original.decode("utf-8")
        count = text.count(old)
        occurrence = spec.get("occurrence")

        entry = {"path": spec["path"], "old": old, "new": new, "occurrences": count}

        if count == 0:
            entry["status"] = ABSENT
            entry["detail"] = (
                "the string the guard is supposed to be checking is not in the file; "
                "mutate what is actually there"
            )
            report["mutations"].append(entry)
            continue
        if count > 1 and occurrence is None:
            entry["status"] = AMBIGUOUS
            entry["detail"] = (
                f"{count} occurrences and no `occurrence` given. Replacing all of them "
                "can make a document-wide check fail for the wrong reason and report "
                "teeth it does not have (this is the IBM README case). Name the one "
                "the claim owns."
            )
            report["mutations"].append(entry)
            continue

        entry["occurrence"] = occurrence or 1
        mutated = _nth_replace(text, old, new, entry["occurrence"])
        if mutated is None:
            entry["status"] = ABSENT
            entry["detail"] = f"fewer than {entry['occurrence']} occurrences to mutate"
            report["mutations"].append(entry)
            continue
        if mutated == text:
            entry["status"] = ABSENT
            entry["detail"] = "the mutation changes nothing — `old` and `new` are equal"
            report["mutations"].append(entry)
            continue

        try:
            target.write_bytes(mutated.encode("utf-8"))
            passed, output = run_test(root, selector, python)
        finally:
            target.write_bytes(original)
            if target.read_bytes() != original:
                report["restored"] = False

        entry["status"] = UNCAUGHT if passed else CAUGHT
        if passed:
            entry["detail"] = (
                "the guard passed with the value wrong, so it does not check what it "
                "reads as checking"
            )
        else:
            entry["failure"] = output.strip()[-600:]
        report["mutations"].append(entry)

    report["verdict"] = _verdict(report["mutations"])
    return report


def _verdict(entries):
    if not entries:
        return INCONCLUSIVE
    statuses = {e["status"] for e in entries}
    if statuses & {UNCAUGHT}:
        return TOOTHLESS
    if statuses & {ABSENT, AMBIGUOUS}:
        return INCONCLUSIVE
    return HAS_TEETH


def format_probe(report):
    """Plain-text report. The verdict is the first line; detail follows."""
    lines = [f"mutation probe — {report['test']}"]
    lines.append(f"  verdict: {report['verdict'].upper()}  (baseline {report['baseline']})")
    if report.get("detail"):
        lines.append(f"  {report['detail']}")
    for e in report["mutations"]:
        where = f"{e['path']} [{e['occurrences']} occurrence(s)]"
        lines.append(f"  {e['status']:>9}  {where}")
        lines.append(f"             {e['old']!r} -> {e['new']!r}")
        if e.get("detail"):
            lines.append(f"             {e['detail']}")
    if not report["restored"]:
        lines.append("  ⚠️  A MUTATED FILE WAS NOT RESTORED — check `git status` before committing.")
    return "\n".join(lines) + "\n"
