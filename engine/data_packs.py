import hashlib
import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACK_PATHS = (
    "sources/registry.yaml",
    "sources/manifest.json",
    "evidence",
    "extractions",
    "calibrations",
    "taxonomies",
    "threat_library",
    "risk_modules",
    "schemas",
)


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
