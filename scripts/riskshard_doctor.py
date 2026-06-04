#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if (
    sys.prefix == sys.base_prefix
    and VENV_PYTHON.exists()
    and Path(sys.executable) != VENV_PYTHON
):
    os.execv(
        str(VENV_PYTHON),
        [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
    )

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.doctor import build_doctor_report, format_doctor_report  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run RiskShard local readiness doctor checks.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run-tests", action="store_true", help="Run the full unittest suite.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = build_doctor_report(ROOT, run_tests=args.run_tests)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_doctor_report(report), end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
