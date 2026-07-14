# Release Proofs

This directory stores small release-readiness proof artifacts that are
intentionally committed for review.

Generate clean-install proof with:

```bash
python scripts/clean_install_proof.py --recreate
```

The proof creates a fresh virtual environment, installs the local checkout, and
runs installed console commands against the checkout via `RISKSHARD_ROOT`.
