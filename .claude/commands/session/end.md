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

3. Reconcile the internal working doc so the next session boots clean:
   - `docs/internal/NEXT_STEPS.md` — mark completed objectives done; append ONE
     session-log line (absolute date + what shipped); ensure the active queue reflects
     reality; and update the restart point's **narrative** / current top blocker (or state
     "no active objective, no blocker"). Capabilities changed? Update the README, not here.
   - **Do not type the repo-state facts** — branch, sha, parity, release, test count, gate
     and doctor lines. Those are generated in step 6; writing them here is what went stale
     three closes in a row.
   - If a doc edit is the only change, commit it (`-s`) so state is durable.

4. Surface, don't bury:
   - any incomplete or deferred work, and where it now lives in the queue;
   - any strategic decision taken without an owner doc, or one still needed
     (`docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control);
   - anything flagged-but-not-done this session.

5. Write a tight close-out: what shipped, what is queued, and what needs me next.

6. **Last, after every other state change — generate the restart point:**

   ```bash
   python scripts/session_state.py --write --run-tests
   ```

   It measures branch, parity, tree, release, suite, gates and the doctor, and splices the
   block at the head of `## Restart point`. Read what it wrote; commit it (`-s`).
   **If anything changes repo state after this — a release cut, a PR merged, a commit — run
   it again.** That ordering is the whole point: the three stale restart points before
   2026-11-21 were each written before the session's last state change, and the worst of them
   was false within the hour because the release was cut after it. The doctor's
   `restart point` check is the backstop, not the fix.

Rule: the session is not "closed" until the tree is clean, open work is reported, the gates
are green (or the reds are named), the owner docs match reality, and the restart point was
generated *after* the last thing that changed the repository.
