---
description: RiskShard session-close ritual — verify nothing is lost, prove the DoD, reconcile the owner docs, summarize.
---

Run the RiskShard session-close ritual. Leave the repo resumable and honest before
we end. Do not skip a step to save time; the point is that the next `/session:start`
orients correctly and no work is silently dropped.

1. Confirm nothing is lost or unreported:
   - `git status -s` — the tree must be clean. Commit anything real (`-s`, on a
     branch, per `AGENTS.md`), or surface it explicitly. Never end on a dirty tree.
   - `git branch` and `gh pr list --state open` — report every unmerged local branch
     and open PR by name; do not leave work invisible.
   - `git fetch origin && git log --oneline origin/main -1` — confirm local `main`
     matches `origin/main`; flag divergence.

2. Prove the definition of done still holds (see `AGENTS.md`):
   - full test suite (`python -m unittest discover -s tests`),
     `validate_evidence.py`, `contributor_preflight.py`, `riskshard_doctor.py`.
   - Report the result honestly. If anything is red, say so — do not close over a failure.

3. Reconcile the owner docs so the next session boots clean:
   - `docs/NEXT_STEPS.md` — mark completed objectives done; append ONE session-log
     line (absolute date + what shipped); ensure the active queue reflects reality.
   - `docs/HANDOVER_STOPPING_POINT.md` — update the restart pointer and the current
     top blocker (or state "no active objective, no blocker").
   - `docs/PROJECT_STATUS.md` — update only if capabilities or known gaps changed.
   - If a doc edit is the only change, commit it (`-s`) so state is durable.

4. Surface, don't bury:
   - any incomplete or deferred work, and where it now lives in the queue;
   - any strategic decision taken without an owner doc, or one still needed
     (`docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control);
   - anything flagged-but-not-done this session.

5. Write a tight close-out: what shipped, what is queued, and what needs me next.

Rule: the session is not "closed" until the tree is clean, open work is reported,
the gates are green (or the reds are named), and the owner docs match reality.
