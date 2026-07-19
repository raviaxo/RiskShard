#!/usr/bin/env python3
"""Generate a branded HTML coverage & confidence dashboard from the shard data.

An executive-at-a-glance view that doubles as a contributor recruiter: it shows
each shard's data strength and where new evidence helps most. Reproducible from
the repo, so it never drifts.
"""
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.coverage import build_coverage_report, render_coverage_html  # noqa: E402


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    output = Path(argv[0]) if argv else ROOT / "results" / "coverage_map.html"
    report = build_coverage_report(ROOT)
    html = render_coverage_html(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Coverage map written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
