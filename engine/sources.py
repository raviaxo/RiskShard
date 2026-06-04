import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import yaml


REQUIRED_SOURCE_FIELDS = {
    "id",
    "title",
    "publisher",
    "source_type",
    "url",
    "publication_date",
    "access_mode",
    "intended_use",
    "usage_notes",
}

CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "application/json": ".json",
    "text/csv": ".csv",
    "text/plain": ".txt",
}


class RedirectHandler(HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, code, msg, headers)


class SourceRegistryError(ValueError):
    pass


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_source_registry(path):
    path = Path(path)
    with open(path, "r") as f:
        registry = yaml.safe_load(f)

    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        raise SourceRegistryError("source registry must contain a sources list")

    seen_ids = set()
    for source in registry["sources"]:
        validate_source(source, seen_ids)
        seen_ids.add(source["id"])

    return registry


def validate_source(source, seen_ids=None):
    if not isinstance(source, dict):
        raise SourceRegistryError("source entries must be mappings")

    missing = REQUIRED_SOURCE_FIELDS - set(source)
    if missing:
        raise SourceRegistryError(
            f"source {source.get('id', '<unknown>')} is missing required fields: {sorted(missing)}"
        )

    source_id = source["id"]
    if not isinstance(source_id, str) or not source_id:
        raise SourceRegistryError("source id must be a non-empty string")
    if seen_ids is not None and source_id in seen_ids:
        raise SourceRegistryError(f"duplicate source id: {source_id}")

    parsed_url = urlparse(source["url"])
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise SourceRegistryError(f"source {source_id} must use an http(s) URL")

    try:
        datetime.strptime(str(source["publication_date"]), "%Y-%m-%d")
    except ValueError as exc:
        raise SourceRegistryError(
            f"source {source_id} publication_date must use YYYY-MM-DD"
        ) from exc

    if not isinstance(source["intended_use"], list) or not source["intended_use"]:
        raise SourceRegistryError(f"source {source_id} intended_use must be a non-empty list")

    if "active" in source and not isinstance(source["active"], bool):
        raise SourceRegistryError(f"source {source_id} active must be true or false")


def active_sources(registry):
    return [
        source for source in registry["sources"]
        if source.get("active", True)
    ]


def raw_filename_for_source(source, content_type=None):
    source_id = source["id"]
    extension = extension_for_content(source["url"], content_type)
    return f"{source_id}{extension}"


def extension_for_content(url, content_type=None):
    if content_type:
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type in CONTENT_TYPE_EXTENSIONS:
            return CONTENT_TYPE_EXTENSIONS[media_type]

    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix and len(suffix) <= 10 and suffix[1:].isalnum():
        return suffix

    return ".bin"


def build_success_record(source, *, gathered_at, final_url, http_status, headers, payload, raw_path):
    content_type = headers.get("Content-Type") or headers.get("content-type")
    return {
        **base_manifest_fields(source, gathered_at),
        "status": "fetched",
        "final_url": final_url,
        "http_status": http_status,
        "content_type": content_type,
        "content_length": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_path": manifest_path(raw_path),
    }


def build_error_record(source, *, gathered_at, error):
    return {
        **base_manifest_fields(source, gathered_at),
        "status": "error",
        "final_url": None,
        "http_status": None,
        "content_type": None,
        "content_length": 0,
        "sha256": None,
        "raw_path": None,
        "error": str(error),
        "attempted_urls": source_urls(source),
    }


def base_manifest_fields(source, gathered_at):
    return {
        "id": source["id"],
        "title": source["title"],
        "publisher": source["publisher"],
        "source_type": source["source_type"],
        "url": source["url"],
        "publication_date": source["publication_date"],
        "gathered_at": gathered_at,
        "access_mode": source["access_mode"],
        "intended_use": source["intended_use"],
        "usage_notes": source["usage_notes"],
    }


def manifest_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def source_urls(source):
    urls = [source["url"]]
    for url in source.get("fallback_urls", []):
        if url not in urls:
            urls.append(url)
    return urls


def build_request(url):
    return Request(
        url,
        headers={
            "User-Agent": "RiskShardSourceGatherer/0.1 (+https://github.com/raviaxo/RiskShard)",
            "Accept": "application/pdf,text/html,application/json,text/plain,*/*",
            "Connection": "close",
        },
    )


def fetch_url(url, *, timeout):
    opener = build_opener(RedirectHandler)
    with opener.open(build_request(url), timeout=timeout) as response:
        return {
            "payload": response.read(),
            "final_url": response.geturl(),
            "http_status": response.getcode(),
            "headers": dict(response.headers.items()),
        }


def fetch_source(source, raw_dir, *, gathered_at=None, timeout=30, retries=1):
    gathered_at = gathered_at or utc_now_iso()
    raw_dir = Path(raw_dir)
    errors = []

    for url in source_urls(source):
        for attempt in range(retries + 1):
            try:
                response = fetch_url(url, timeout=timeout)
                payload = response["payload"]
                final_url = response["final_url"]
                http_status = response["http_status"]
                headers = response["headers"]
                break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                errors.append(f"{url} attempt {attempt + 1}: {exc}")
        else:
            continue
        break
    else:
        return build_error_record(
            source,
            gathered_at=gathered_at,
            error="; ".join(errors),
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    content_type = headers.get("Content-Type") or headers.get("content-type")
    raw_path = raw_dir / raw_filename_for_source(source, content_type)
    raw_path.write_bytes(payload)

    return build_success_record(
        source,
        gathered_at=gathered_at,
        final_url=final_url,
        http_status=http_status,
        headers=headers,
        payload=payload,
        raw_path=raw_path,
    )


def gather_sources(registry_path, raw_dir, *, timeout=30, retries=1):
    registry = load_source_registry(registry_path)
    generated_at = utc_now_iso()
    records = [
        fetch_source(source, raw_dir, gathered_at=generated_at, timeout=timeout, retries=retries)
        for source in active_sources(registry)
    ]

    return {
        "manifest_version": "1.0",
        "generated_at": generated_at,
        "source_count": len(records),
        "fetched_count": sum(1 for record in records if record["status"] == "fetched"),
        "error_count": sum(1 for record in records if record["status"] == "error"),
        "sources": records,
    }


def write_manifest(manifest, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output_path
