#!/usr/bin/env python3
"""Reading aid for the ADR-0015 source audit. It does not decide anything.

For each gathered artifact this pulls the passages that bear on the four audit
properties and prints them with context, so a human can answer from the source's own
words instead of hunting a 200-page PDF.

**It is not the verification.** The audit's whole design rests on a source-level claim
resting on a source-level read (ADR-0015 part 2), and a keyword hit is not a read: a
report can say "distribution" about a bar chart of incident counts, or "median" about
response time rather than loss. Every answer written into `sources/audit.yaml` is a
judgement made after reading the passages this prints, and the passage is quoted in
the answer's `detail` so a reader can disagree with the judgement rather than take it.

Usage:
    python docs/internal/research/source_property_scan.py            # all sources
    python docs/internal/research/source_property_scan.py verizon    # id substring
"""
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Patterns per property. Deliberately wide: a miss costs a wrong answer, a false hit
# costs a few seconds of reading. `mode` is narrow because "mode" is a common English
# word ("spectator mode") — the modal-value senses are what matter.
PATTERNS = {
    "mode": r"\bmodal\b|most likely (?:value|loss|cost|outcome)|\bthe mode\b|most common (?:loss|cost|value)",
    "distribution": r"\bdistribution\b|\bquantile\b|\bpercentile\b|\bdecile\b|\bquartile\b|\bhistogram\b|cumulative density|\bCCDF\b|interquartile",
    "exceedance": r"\bexceed|\bexceedance\b|probability of a loss|\bworse than\b|\btail\b|return period|\b9[05]th\b",
    "population": r"\bn\s*=\s*[\d,]+|\bsample\b|respondents|\bsurveyed\b|\bpopulation\b|\bmethodolog",
}

CONTEXT = 220


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def extract_text(path):
    """Artifact -> plain text. Returns None when the format cannot be read here."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            out = subprocess.run(["pdftotext", "-q", str(path), "-"],
                                 capture_output=True, text=True, timeout=180)
            return out.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
    if suffix in (".html", ".htm"):
        parser = _Text()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        return " ".join(parser.parts)
    if suffix in (".json", ".txt", ".csv"):
        return path.read_text(encoding="utf-8", errors="replace")
    return None  # xlsx, zip — not readable as text here; read by hand


def scan(text, limit=4):
    """Passages bearing on each property, deduped and trimmed."""
    flat = " ".join((text or "").split())
    found = {}
    for prop, pattern in PATTERNS.items():
        hits, seen = [], set()
        for m in re.finditer(pattern, flat, re.I):
            start = max(0, m.start() - CONTEXT // 2)
            passage = flat[start:start + CONTEXT]
            key = passage[:60].lower()
            if key in seen:
                continue
            seen.add(key)
            hits.append(passage)
            if len(hits) >= limit:
                break
        found[prop] = hits
    return found


def main(argv):
    needle = argv[1].lower() if len(argv) > 1 else ""
    manifest = json.loads((ROOT / "sources" / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["sources"]:
        sid = entry["id"]
        if needle and needle not in sid.lower():
            continue
        path = ROOT / entry.get("raw_path", "")
        if not path.exists():
            print(f"\n{'=' * 78}\n{sid}\n  NO ARTIFACT at {entry.get('raw_path')}")
            continue
        text = extract_text(path)
        print(f"\n{'=' * 78}\n{sid}  [{entry.get('publisher')}]  {path.suffix} "
              f"{path.stat().st_size // 1024}KB")
        if text is None:
            print("  UNREADABLE HERE — read by hand")
            continue
        print(f"  words: {len(text.split()):,}")
        for prop, hits in scan(text).items():
            print(f"  --- {prop} ({len(hits)} passage(s))")
            for h in hits:
                print(f"      … {h.strip()} …")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
