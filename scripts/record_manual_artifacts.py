#!/usr/bin/env python3
"""Record the artifacts a person obtained by hand, without re-gathering the rest.

13 of the sources the audit still owes sit behind a registration wall or a form.
`gather_sources.py` cannot reach them, and pointing it at their landing pages is
worse than leaving them alone: the page returns HTTP 200, the manifest records a
new sha256, and the real document is silently replaced.

So those sources are declared `access_mode: manual_download` in the registry, a
person puts the file in `sources/raw/<source_id>.<ext>`, and this merges its record
into the manifest — same sha256 discipline as a gathered artifact, and saying how it
was acquired rather than claiming a fetch that never happened.

It is deliberately narrow. It only ever touches rows whose source declares
`manual_download`, so it cannot disturb a gathered artifact, and running it is safe
at any time. Re-running after replacing a file updates that row's hash.

    python scripts/record_manual_artifacts.py           # merge them in
    python scripts/record_manual_artifacts.py --check   # report, change nothing
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.sources import (  # noqa: E402
    MANUAL_ACCESS_MODES,
    build_manual_record,
    build_missing_manual_record,
    load_source_registry,
    utc_now_iso,
)

SUFFIXES = (".pdf", ".html", ".xlsx", ".csv", ".json", ".zip")


def find_artifact(raw_dir, source_id):
    for suffix in SUFFIXES:
        candidate = raw_dir / f"{source_id}{suffix}"
        if candidate.exists():
            return candidate
    return raw_dir / f"{source_id}.pdf"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=ROOT / "sources" / "manifest.json")
    parser.add_argument("--registry", type=Path, default=ROOT / "sources" / "registry.yaml")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "sources" / "raw")
    parser.add_argument("--check", action="store_true",
                        help="report what would change and write nothing")
    args = parser.parse_args(argv)

    registry = load_source_registry(args.registry)
    sources = registry["sources"] if isinstance(registry, dict) else registry
    manual = [s for s in sources if s.get("access_mode") in MANUAL_ACCESS_MODES]
    if not manual:
        print("No source declares access_mode: manual_download.")
        return 0

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    by_id = {row.get("id"): row for row in manifest["sources"]}
    gathered_at = utc_now_iso()

    added = updated = missing = 0
    for source in manual:
        path = find_artifact(args.raw_dir, source["id"])
        if path.exists():
            record = build_manual_record(source, gathered_at=gathered_at,
                                         raw_path=path, payload=path.read_bytes())
            previous = by_id.get(source["id"])
            if previous is None:
                added += 1
                print(f"  + {source['id']}  {record['sha256'][:16]}…  {path.name}")
            elif previous.get("sha256") != record["sha256"]:
                updated += 1
                print(f"  ~ {source['id']}  hash changed — the document was replaced")
            else:
                continue
            by_id[source["id"]] = record
        else:
            missing += 1
            print(f"  ! {source['id']}  no artifact at {path.name} — still owed")
            by_id[source["id"]] = build_missing_manual_record(
                source, gathered_at=gathered_at, expected_path=path)

    if args.check:
        print(f"\ncheck only: {added} to add, {updated} to update, {missing} still owed")
        return 1 if missing else 0

    manifest["sources"] = sorted(by_id.values(), key=lambda r: r.get("id") or "")
    manifest["source_count"] = len(manifest["sources"])
    manifest["fetched_count"] = sum(1 for r in manifest["sources"] if r.get("status") == "fetched")
    manifest["error_count"] = sum(1 for r in manifest["sources"] if r.get("status") == "error")
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    print(f"\nManifest updated: {added} added, {updated} updated, {missing} still owed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
