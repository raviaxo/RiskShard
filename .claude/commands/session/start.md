---
description: RiskShard session-open ritual — orient from the owner docs, confirm repo reality, state one objective.
argument-hint: [optional framing for the session]
---

Run the RiskShard session-open ritual. This is load-bearing: do not write product
code before completing it.

1. Read, in order:
   - `AGENTS.md` (operating rules and definition of done)
   - `docs/internal/NEXT_STEPS.md` — its header gives the restart point, current top
     blocker, canonical-owner pointers, and maturity ladder; its tail is the active queue.
     (Capabilities live in the README; live coverage in the readiness tools.)
     The restart point opens with a **generated** block of repo state. Trust it only as far
     as its stated measurement date, and confirm it in step 2 — if the doctor's
     `restart point` check reads `needs_review`, that block has been overtaken: report the
     drift rather than repeating it.
2. Confirm repo reality — do not trust memory:
   - `git log --oneline -5` and `git status -s`
   - `git fetch origin && git log --oneline origin/main -3`; flag any divergence.
3. Verify the environment is runnable (Python ≥ 3.9). Activate `.venv`; if missing,
   create it (`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`).
4. State the **ONE** objective for this session in a single sentence, name the files
   it will touch, and **wait for my confirmation** before editing anything.

Rules:
- Surface divergence between assumption and repo reality before proposing work.
- One objective only. New important items go to `docs/internal/NEXT_STEPS.md`, not into scope.
- If a strategic decision is needed and no owner doc records it, surface it and stop
  (see `docs/PUBLISHABLE_REQUIREMENTS.md` → Change Control).

Session framing (optional): $ARGUMENTS
