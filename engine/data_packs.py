import hashlib
import json
from datetime import datetime
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RELEASE_DIR = PROJECT_ROOT / "data_pack_releases"
# What a released data pack is fingerprinted over. `scenarios` was missing until
# 2026-07-30: a scenario file holds the values the Monte Carlo actually runs, so the
# fingerprint that anchors releases and pins citations (ADR-0004) did not cover the
# numbers being published. The calibration-drift found this week could have sat inside a
# released pack without changing its fingerprint.
PACK_PATHS = (
    "sources/registry.yaml",
    "sources/manifest.json",
    "evidence",
    "extractions",
    "calibrations",
    "scenarios",
    "taxonomies",
    "threat_library",
    "risk_modules",
    "schemas",
)
VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def build_data_pack_manifest(root=PROJECT_ROOT, pack_paths=PACK_PATHS):
    root = Path(root)
    files = []
    digest = hashlib.sha256()

    for path_value in pack_paths:
        path = root / path_value
        for file_path in iter_pack_files(path):
            rel_path = file_path.relative_to(root).as_posix()
            payload = file_path.read_bytes()
            file_hash = hashlib.sha256(payload).hexdigest()
            digest.update(rel_path.encode("utf-8"))
            digest.update(file_hash.encode("utf-8"))
            files.append({
                "path": rel_path,
                "sha256": file_hash,
                "size_bytes": len(payload),
            })

    files.sort(key=lambda item: item["path"])
    return {
        "pack_version": datetime.now().strftime("%Y.%m.%d"),
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "file_count": len(files),
        "fingerprint": digest.hexdigest(),
        "paths": list(pack_paths),
        "files": files,
    }


def iter_pack_files(path):
    path = Path(path)
    if not path.exists():
        return []
    if path.is_file():
        return [path]
    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file()
        and not file_path.name.startswith(".")
        and "__pycache__" not in file_path.parts
    )


def write_data_pack_manifest(manifest, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output_path


def build_data_pack_release(root=PROJECT_ROOT, *, version=None, notes=None):
    manifest = build_data_pack_manifest(root)
    release_version = version or manifest["pack_version"]
    validate_release_version(release_version)
    return {
        "release_type": "riskshard_data_pack_release",
        "release_version": release_version,
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
        "pack_version": manifest["pack_version"],
        "fingerprint": manifest["fingerprint"],
        "file_count": manifest["file_count"],
        "source_manifest_path": "sources/manifest.json",
        "source_manifest_sha256": file_sha256(Path(root) / "sources" / "manifest.json"),
        "notes": notes or "Named local data-pack release artifact.",
        "manifest": manifest,
    }


def write_data_pack_release(release, output_dir=DEFAULT_RELEASE_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{release['release_version']}.json"
    output_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    return output_path


def validate_release_version(version):
    if not VERSION_PATTERN.match(str(version)):
        raise ValueError(
            "release version must start with an alphanumeric character and "
            "contain only letters, numbers, dots, underscores, or hyphens"
        )


def file_sha256(path):
    path = Path(path)
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_data_pack_release(release, max_files=8):
    lines = [
        "Data pack release",
        f"Release: {release['release_version']}",
        f"Fingerprint: {release['fingerprint']}",
        f"Files: {release['file_count']}",
        f"Notes: {release['notes']}",
        "",
        "Included paths:",
    ]
    for path in release["manifest"]["paths"]:
        lines.append(f"- {path}")
    lines.extend(["", "Sample files:"])
    for item in release["manifest"]["files"][:max_files]:
        lines.append(f"- {item['path']} {item['sha256'][:12]}")
    if len(release["manifest"]["files"]) > max_files:
        lines.append(f"- ... {len(release['manifest']['files']) - max_files} more")
    return "\n".join(lines) + "\n"


def format_data_pack_manifest(manifest, max_files=8):
    lines = [
        "Data pack manifest",
        f"Version: {manifest['pack_version']}",
        f"Fingerprint: {manifest['fingerprint']}",
        f"Files: {manifest['file_count']}",
        "",
        "Included paths:",
    ]
    for path in manifest["paths"]:
        lines.append(f"- {path}")
    lines.extend(["", "Sample files:"])
    for item in manifest["files"][:max_files]:
        lines.append(f"- {item['path']} {item['sha256'][:12]}")
    if len(manifest["files"]) > max_files:
        lines.append(f"- ... {len(manifest['files']) - max_files} more")
    return "\n".join(lines) + "\n"
