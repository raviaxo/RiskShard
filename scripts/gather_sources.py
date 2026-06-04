#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.sources import gather_sources, write_manifest  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gather curated source materials and write a provenance manifest."
    )
    parser.add_argument(
        "--registry",
        default=ROOT / "sources" / "registry.yaml",
        type=Path,
        help="YAML source registry to gather.",
    )
    parser.add_argument(
        "--raw-dir",
        default=ROOT / "sources" / "raw",
        type=Path,
        help="Directory for raw downloaded artifacts. This is ignored by Git.",
    )
    parser.add_argument(
        "--manifest",
        default=ROOT / "sources" / "manifest.json",
        type=Path,
        help="Manifest JSON path to write.",
    )
    parser.add_argument(
        "--timeout",
        default=30,
        type=int,
        help="Per-source fetch timeout in seconds.",
    )
    parser.add_argument(
        "--retries",
        default=1,
        type=int,
        help="Retry attempts per source URL before trying the next fallback URL.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = gather_sources(args.registry, args.raw_dir, timeout=args.timeout, retries=args.retries)
    output_path = write_manifest(manifest, args.manifest)

    print(f"Source manifest written: {output_path}")
    print(
        "Fetched "
        f"{manifest['fetched_count']} of {manifest['source_count']} sources "
        f"({manifest['error_count']} errors)."
    )

    for source in manifest["sources"]:
        if source["status"] == "fetched":
            print(f"- {source['id']}: fetched {source['content_length']} bytes")
        else:
            print(f"- {source['id']}: ERROR {source.get('error')}")

    return 0 if manifest["fetched_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
