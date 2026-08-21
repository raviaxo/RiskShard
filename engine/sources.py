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

# Whether a source URL is edition-stable or serves whatever is current.
#
# Added 2026-07-31 after ibm.com/reports/data-breach -- registered as the 2025 Cost of a
# Data Breach Report -- silently began serving the 2026 edition. The evidence cited USD
# 4.4M; the gathered artifact said USD 4.99M; the cited figure appeared nowhere in its own
# evidence. Nothing detected it. The access-mode guard could not: HTML was still HTML, and
# the only visible symptom was a 23% drop in byte count spotted by accident.
#
#   dated    the URL is edition-specific and will keep serving this edition
#            (a dated press release, a versioned PDF, an archived snapshot)
#   rolling  the URL always serves the current edition, so the artifact will drift away
#            from the citation and the record needs re-verification when it does
#   unknown  not yet assessed (the default, so this is additive rather than a migration)
URL_STABILITY_VALUES = {"dated", "rolling", "unknown"}

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

    stability = source.get("url_stability", "unknown")
    if stability not in URL_STABILITY_VALUES:
        raise SourceRegistryError(
            f"source {source_id} url_stability must be one of "
            f"{sorted(URL_STABILITY_VALUES)}, got {stability!r}"
        )

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


# What each declared access mode should actually come back as. A registry URL that
# points at a landing page instead of the artifact returns HTML with HTTP 200, which
# looks like success: the manifest records a new sha256 and raw_path, and the real
# evidence artifact is silently replaced. That happened to the NetDiligence claims
# study on 2026-07-30 -- a 9.1MB PDF became an 83KB HTML page -- and would have
# invalidated the evidence citing it.
ACCESS_MODE_CONTENT = {
    "public_pdf": ("application/pdf",),
    "public_html": ("text/html", "application/xhtml"),
    "public_json": ("application/json", "text/json"),
    "public_csv": ("text/csv", "application/csv", "text/plain"),
    "public_zip": ("application/zip", "application/x-zip-compressed"),
}


def content_matches_access_mode(access_mode, content_type, payload=b""):
    """Does the fetched body match what the registry said this source is?"""
    expected = ACCESS_MODE_CONTENT.get(access_mode)
    if not expected:
        return True
    media_type = (content_type or "").split(";", 1)[0].strip().lower()
    if any(media_type.startswith(prefix) for prefix in expected):
        return True
    # Some servers mislabel a genuine PDF; trust the magic bytes over the header.
    if access_mode == "public_pdf" and payload[:5] == b"%PDF-":
        return True
    return False



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


MANUAL_ACCESS_MODES = frozenset({"manual_download"})


def build_manual_record(source, *, gathered_at, raw_path, payload):
    """An artifact a person obtained, recorded so anyone else can recheck it.

    13 of the sources still owed to the audit sit behind a registration wall, a
    click-through, or a form. The gatherer cannot reach them, and re-running it
    against their landing page is worse than not running it at all: the page returns
    HTTP 200, the manifest records a new sha256, and the real document is silently
    replaced. That is the NetDiligence failure described at the top of this module.

    So a source declared `access_mode: manual_download` is never fetched. Its record
    is built from the file already on disk, carries the same sha256 discipline as a
    gathered one, and says plainly how it was acquired rather than claiming a fetch
    that did not happen.
    """
    return {
        **base_manifest_fields(source, gathered_at),
        "status": "fetched",
        "acquisition": "manual_download",
        "final_url": None,
        "http_status": None,
        "content_type": content_type_for_path(raw_path),
        "content_length": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_path": manifest_path(raw_path),
    }


def build_missing_manual_record(source, *, gathered_at, expected_path):
    """Declared as hand-obtained, and the file is not there.

    Reported as an error rather than skipped: a source whose artifact is absent must
    not read as one nobody has got round to.
    """
    return {
        **base_manifest_fields(source, gathered_at),
        "status": "error",
        "acquisition": "manual_download",
        "final_url": None,
        "http_status": None,
        "content_type": None,
        "content_length": 0,
        "sha256": None,
        "raw_path": None,
        "error": (f"declared access_mode: manual_download but no artifact at "
                  f"{manifest_path(expected_path)} — obtain it and place it there"),
        "attempted_urls": source_urls(source),
    }


def content_type_for_path(path):
    suffix = Path(path).suffix.lower()
    return {".pdf": "application/pdf",
            ".html": "text/html",
            ".htm": "text/html",
            ".json": "application/json",
            ".csv": "text/csv",
            ".zip": "application/zip",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }.get(suffix, "application/octet-stream")


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
        "url_stability": source.get("url_stability", "unknown"),
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

    # Gated sources are never fetched: see build_manual_record.
    if source.get("access_mode") in MANUAL_ACCESS_MODES:
        expected = raw_dir / f"{source['id']}{Path(source.get('artifact_suffix') or '.pdf').suffix}"
        if expected.exists():
            return build_manual_record(source, gathered_at=gathered_at,
                                       raw_path=expected, payload=expected.read_bytes())
        return build_missing_manual_record(source, gathered_at=gathered_at,
                                           expected_path=expected)

    errors = []

    fetched = None
    for url in source_urls(source):
        for attempt in range(retries + 1):
            try:
                response = fetch_url(url, timeout=timeout)
                break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                errors.append(f"{url} attempt {attempt + 1}: {exc}")
        else:
            continue

        content_type = response["headers"].get("Content-Type") or response["headers"].get("content-type")
        if not content_matches_access_mode(source["access_mode"], content_type, response["payload"]):
            # Not the artifact. Record why and try the next URL rather than writing a
            # landing page over a previously gathered document.
            errors.append(
                f"{url}: declared access_mode {source['access_mode']} but the server "
                f"returned {(content_type or 'no content-type')!r} "
                f"({len(response['payload'])} bytes); this URL looks like a landing page "
                "rather than the artifact"
            )
            continue

        fetched = response
        break

    if fetched is None:
        return build_error_record(
            source,
            gathered_at=gathered_at,
            error="; ".join(errors),
        )

    payload = fetched["payload"]
    final_url = fetched["final_url"]
    http_status = fetched["http_status"]
    headers = fetched["headers"]
    content_type = headers.get("Content-Type") or headers.get("content-type")

    raw_dir.mkdir(parents=True, exist_ok=True)
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
