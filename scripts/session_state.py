#!/usr/bin/env python3
"""Print, or write, the generated restart point for docs/internal/NEXT_STEPS.md.

Thin by design: everything it knows lives in engine/session_state.py.
"""
import argparse
import json
import os
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def reexec_venv_if_needed():
    if (
        sys.prefix == sys.base_prefix
        and VENV_PYTHON.exists()
        and Path(sys.executable) != VENV_PYTHON
    ):
        os.execv(
            str(VENV_PYTHON),
            [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
        )


if __name__ == "__main__":
    reexec_venv_if_needed()

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.session_state import (  # noqa: E402
    collect_session_state,
    render_restart_point,
    restart_point_status,
    write_restart_point,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate the NEXT_STEPS restart point from measured repo state.",
    )
    parser.add_argument("--write", action="store_true",
                        help="Splice the block into docs/internal/NEXT_STEPS.md.")
    parser.add_argument("--run-tests", action="store_true",
                        help="Run the full suite so the test line is a result, not a count.")
    parser.add_argument("--check", action="store_true",
                        help="Report drift between the recorded block and live state.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.check:
        status = restart_point_status(ROOT)
        if args.json:
            print(json.dumps(status, indent=2, sort_keys=True))
        else:
            for line in status["drift"]:
                print(f"drift: {line}")
            if not status["drift"]:
                recorded = status["recorded"] or {}
                print(f"restart point matches live state "
                      f"(measured {recorded.get('generated_at', '?')})")
        return 1 if status["drift"] else 0

    if args.write:
        path, block = write_restart_point(ROOT, run_tests=args.run_tests)
        print(f"wrote {path.relative_to(ROOT)}")
        print()
        print(block, end="")
        return 0

    state = collect_session_state(ROOT, run_tests=args.run_tests)
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True))
    else:
        print(render_restart_point(state), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
