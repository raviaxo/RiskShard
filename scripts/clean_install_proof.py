#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.clean_install import (  # noqa: E402
    DEFAULT_PROOF_PATH,
    DEFAULT_VENV_PATH,
    build_clean_install_proof,
    format_clean_install_proof,
    load_clean_install_proof,
    sanitize_text,
    write_clean_install_proof,
)
from engine.project_paths import find_project_root  # noqa: E402


ROOT = find_project_root(fallback=SCRIPT_ROOT)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Verify RiskShard from a clean virtual environment.")
    parser.add_argument(
        "--venv",
        default=DEFAULT_VENV_PATH,
        type=Path,
        help="Clean virtual environment path to create or reuse.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_PROOF_PATH,
        type=Path,
        help="Proof JSON path to write.",
    )
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the venv first.")
    parser.add_argument("--check", action="store_true", help="Only read and print the current proof.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.check:
        proof = load_clean_install_proof(args.output)
    else:
        proof = build_clean_install_proof(ROOT, venv_path=args.venv, recreate=args.recreate)
        proof["path"] = sanitize_text(args.output.as_posix(), ROOT, args.venv)
        write_clean_install_proof(proof, args.output)

    if args.json:
        print(json.dumps(proof, indent=2, sort_keys=True))
    else:
        print(format_clean_install_proof(proof), end="")
        if not args.check:
            print(f"Proof saved: {args.output}")
    return 0 if proof and proof.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
