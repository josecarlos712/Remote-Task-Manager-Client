# -*- coding: utf-8 -*-
"""Download a remote file in a background thread (non-blocking) with progress."""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

import requests

import config
from config import logger

COMMAND_ID = "download_file"
TITLE = "Download File"
DESCRIPTION = (
    "Downloads a file from a URL in a background thread. "
    "Save folder is chosen from config/download_routes.json by URL host "
    "(e.g. civitai.com -> ComfyUI models/downloads)."
)
ARGS = [
    {
        "name": "url",
        "type": "str",
        "required": True,
        "description": "HTTP/HTTPS URL of the file to download.",
    },
    {
        "name": "save_dir",
        "type": "str",
        "required": False,
        "description": "Optional override destination folder (absolute path).",
    },
    {
        "name": "filename",
        "type": "str",
        "required": False,
        "description": "Optional filename. If empty, taken from Content-Disposition header or URL.",
    },
]

# job_id -> status dict (best-effort in-memory tracker)
_DOWNLOADS: dict[str, dict] = {}
_LOCK = threading.Lock()
_MAX_JOBS = 80

_DEFAULT_ROUTES = [
    {
        "match": "civitai.com",
        "dir": r"C:\Users\josec\AppData\Local\Comfy-Desktop\ComfyUI-Shared\models\downloads",
    },
]

_CIVITAI_HOSTS = ("civitai.com", "civitai.red")


def _routes_path() -> Path:
    return Path.cwd() / "config" / "download_routes.json"


def _sensible_dir() -> Path:
    return Path.cwd() / "sensible"


def load_secrets() -> dict:
    """Load private secrets from sensible/secrets.json (never committed)."""
    path = _sensible_dir() / "secrets.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"download_file: could not read sensible/secrets.json: {e}")
        return {}


def _is_civitai_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(h in host for h in _CIVITAI_HOSTS)


def _download_headers(url: str) -> dict:
    headers = {
        "User-Agent": "Remote-Task-Manager-Client/1.0",
    }
    if _is_civitai_url(url):
        key = (load_secrets().get("civitai_api_key") or "").strip()
        if key:
            # Civitai API / gated downloads
            headers["Authorization"] = f"Bearer {key}"
        else:
            logger.warning(
                "download_file: Civitai URL without civitai_api_key in sensible/secrets.json"
            )
    return headers


def load_download_routes() -> list[dict]:
    path = _routes_path()
    if not path.exists():
        return list(_DEFAULT_ROUTES)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception as e:
        logger.warning(f"download_file: could not read download_routes.json: {e}")
    return list(_DEFAULT_ROUTES)


def resolve_save_dir(url: str, override: Optional[str] = None) -> Path:
    if override and str(override).strip():
        return Path(str(override).strip())

    host = (urlparse(url).hostname or "").lower()
    for route in load_download_routes():
        match = str(route.get("match") or "").lower()
        folder = route.get("dir")
        if match and folder and match in host:
            return Path(folder)

    configured = config.get_setting("path_downloads", "downloads") or "downloads"
    path = Path(str(configured))
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _safe_filename(name: str) -> str:
    name = unquote(name or "").strip().replace("\\", "/").split("/")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name)
    name = name.strip(" .")
    return name or f"download_{uuid.uuid4().hex[:8]}"


def _filename_from_url(url: str) -> str:
    path = unquote(urlparse(url).path or "")
    candidate = Path(path).name
    if candidate and "." in candidate:
        return _safe_filename(candidate)
    return ""


def _filename_from_headers(response: requests.Response) -> str:
    """Prefer Content-Disposition (RFC 6266 / filename*)."""
    cd = response.headers.get("Content-Disposition") or ""
    if not cd:
        return ""

    match = re.search(r"filename\*\s*=\s*([^']*)''([^;]+)", cd, flags=re.I)
    if match:
        return _safe_filename(unquote(match.group(2).strip().strip('"')))

    match = re.search(r'filename\s*=\s*"([^"]+)"', cd, flags=re.I)
    if match:
        return _safe_filename(match.group(1))

    match = re.search(r"filename\s*=\s*([^;]+)", cd, flags=re.I)
    if match:
        return _safe_filename(match.group(1).strip().strip('"'))
    return ""


def _public_job(job_id: str, job: dict) -> dict:
    written = int(job.get("bytes_written") or 0)
    total = job.get("bytes_total")
    total_i = int(total) if total else 0
    progress = None
    if total_i > 0:
        progress = min(100.0, round(100.0 * written / total_i, 1))
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "url": job.get("url"),
        "filename": job.get("filename"),
        "path": job.get("path"),
        "save_dir": job.get("save_dir"),
        "bytes_written": written,
        "bytes_total": total_i or None,
        "progress_pct": progress,
        "speed_bps": job.get("speed_bps") or 0,
        "message": job.get("message"),
        "started_at": job.get("started_at"),
        "updated_at": job.get("updated_at"),
        "finished_at": job.get("finished_at"),
    }


def _set_job(job_id: str, **fields) -> None:
    with _LOCK:
        current = _DOWNLOADS.get(job_id, {})
        current.update(fields)
        current["updated_at"] = time.time()
        _DOWNLOADS[job_id] = current
        if len(_DOWNLOADS) > _MAX_JOBS:
            # Drop oldest finished/error jobs first
            ordered = sorted(
                _DOWNLOADS.items(),
                key=lambda kv: kv[1].get("updated_at") or kv[1].get("started_at") or 0,
            )
            while len(_DOWNLOADS) > _MAX_JOBS and ordered:
                jid, meta = ordered.pop(0)
                if meta.get("status") in ("completed", "error"):
                    _DOWNLOADS.pop(jid, None)


def get_download(job_id: str) -> Optional[dict]:
    with _LOCK:
        job = _DOWNLOADS.get(job_id)
        if not job:
            return None
        return _public_job(job_id, job)


def list_downloads(active_only: bool = False) -> list[dict]:
    with _LOCK:
        items = [_public_job(jid, meta) for jid, meta in _DOWNLOADS.items()]
    if active_only:
        items = [j for j in items if j.get("status") in ("queued", "downloading")]
    items.sort(key=lambda j: j.get("started_at") or 0, reverse=True)
    return items


def remove_download(job_id: str) -> tuple[bool, str]:
    """Remove a finished job from the tracker. Active jobs cannot be removed."""
    jid = str(job_id or "").strip()
    if not jid:
        return False, "Missing job_id"
    with _LOCK:
        job = _DOWNLOADS.get(jid)
        if not job:
            return False, "Download job not found"
        status = job.get("status")
        if status in ("queued", "downloading"):
            return False, "Cannot remove an active download"
        _DOWNLOADS.pop(jid, None)
    return True, "Removed"


def cancel_download(job_id: str) -> tuple[bool, str]:
    """Request cancel of a queued/downloading job. Worker stops and cleans .part file."""
    jid = str(job_id or "").strip()
    if not jid:
        return False, "Missing job_id"
    with _LOCK:
        job = _DOWNLOADS.get(jid)
        if not job:
            return False, "Download job not found"
        status = job.get("status")
        if status not in ("queued", "downloading"):
            return False, "Download is not active"
        job["cancel_requested"] = True
        job["message"] = "Cancel requested..."
        job["updated_at"] = time.time()
        _DOWNLOADS[jid] = job
    return True, "Cancel requested"


def _is_cancel_requested(job_id: str) -> bool:
    with _LOCK:
        job = _DOWNLOADS.get(job_id) or {}
        return bool(job.get("cancel_requested"))


def clear_finished_downloads() -> int:
    """Remove all completed/error/cancelled jobs. Returns how many were cleared."""
    removed = 0
    with _LOCK:
        for jid, meta in list(_DOWNLOADS.items()):
            if meta.get("status") in ("completed", "error", "cancelled"):
                _DOWNLOADS.pop(jid, None)
                removed += 1
    return removed


def _download_worker(job_id: str, url: str, save_dir: Path, filename: Optional[str]) -> None:
    tmp_path: Optional[Path] = None
    try:
        if _is_cancel_requested(job_id):
            raise InterruptedError("Download cancelled by user")
        save_dir.mkdir(parents=True, exist_ok=True)
        _set_job(job_id, status="downloading", message="Connecting...", speed_bps=0)

        with requests.get(
            url,
            stream=True,
            timeout=(15, 600),
            allow_redirects=True,
            headers=_download_headers(url),
        ) as response:
            response.raise_for_status()

            # Prefer explicit name, else Content-Disposition, else URL path
            chosen = _safe_filename(filename) if filename else ""
            if not chosen:
                chosen = _filename_from_headers(response) or _filename_from_url(url)
            if not chosen:
                chosen = f"download_{job_id[:8]}"

            dest = save_dir / chosen
            if dest.exists():
                stem, suffix = dest.stem, dest.suffix
                n = 2
                while True:
                    candidate = save_dir / f"{stem}_{n}{suffix}"
                    if not candidate.exists():
                        dest = candidate
                        break
                    n += 1

            tmp_path = dest.with_suffix(dest.suffix + ".part")
            total = int(response.headers.get("Content-Length") or 0)
            written = 0
            started = time.monotonic()
            last_report = 0.0
            last_bytes = 0
            last_speed_t = started

            _set_job(
                job_id,
                status="downloading",
                filename=dest.name,
                path=str(dest),
                bytes_total=total or None,
                bytes_written=0,
                speed_bps=0,
                message=f"Saving to {dest}",
            )

            with open(tmp_path, "wb") as out:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if _is_cancel_requested(job_id):
                        raise InterruptedError("Download cancelled by user")
                    if not chunk:
                        continue
                    out.write(chunk)
                    written += len(chunk)
                    now = time.monotonic()
                    if now - last_report >= 0.25:
                        dt = max(now - last_speed_t, 0.001)
                        instant = (written - last_bytes) / dt
                        avg = written / max(now - started, 0.001)
                        speed = instant if instant > 0 else avg
                        _set_job(
                            job_id,
                            bytes_written=written,
                            speed_bps=int(speed),
                            message=f"Downloading {dest.name}",
                        )
                        last_report = now
                        last_bytes = written
                        last_speed_t = now

            if _is_cancel_requested(job_id):
                raise InterruptedError("Download cancelled by user")

            os.replace(tmp_path, dest)
            tmp_path = None
            elapsed = max(time.monotonic() - started, 0.001)
            _set_job(
                job_id,
                status="completed",
                filename=dest.name,
                path=str(dest),
                bytes_written=written,
                bytes_total=total or written,
                speed_bps=int(written / elapsed),
                finished_at=time.time(),
                message=f"Downloaded {written} bytes -> {dest}",
            )
            logger.info(f"download_file[{job_id}] completed: {dest} ({written} bytes)")
    except InterruptedError:
        logger.info(f"download_file[{job_id}] cancelled")
        _set_job(
            job_id,
            status="cancelled",
            speed_bps=0,
            finished_at=time.time(),
            message="Download cancelled",
            cancel_requested=False,
        )
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
    except Exception as e:
        if _is_cancel_requested(job_id):
            logger.info(f"download_file[{job_id}] cancelled during error path")
            _set_job(
                job_id,
                status="cancelled",
                speed_bps=0,
                finished_at=time.time(),
                message="Download cancelled",
                cancel_requested=False,
            )
        else:
            logger.error(f"download_file[{job_id}] failed: {e}", exc_info=True)
            _set_job(
                job_id,
                status="error",
                message=str(e),
                speed_bps=0,
                finished_at=time.time(),
            )
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def handler(**kwargs):
    url = kwargs.get("url") or kwargs.get("message")
    if not url or not isinstance(url, str):
        return "Missing required argument: url", 400
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return "URL must start with http:// or https://", 400

    save_dir = resolve_save_dir(url, kwargs.get("save_dir"))
    filename = kwargs.get("filename") or None
    if filename is not None:
        filename = str(filename).strip() or None

    job_id = uuid.uuid4().hex
    now = time.time()
    _set_job(
        job_id,
        status="queued",
        url=url,
        save_dir=str(save_dir),
        filename=filename,
        bytes_written=0,
        bytes_total=None,
        speed_bps=0,
        progress_pct=None,
        cancel_requested=False,
        started_at=now,
        message="Queued",
    )

    thread = threading.Thread(
        target=_download_worker,
        args=(job_id, url, save_dir, filename),
        name=f"download-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    logger.info(f"download_file[{job_id}] started url={url} dir={save_dir}")

    return {
        "started": True,
        "job_id": job_id,
        "url": url,
        "save_dir": str(save_dir),
        "filename": filename,
        "message": f"Download started in background. Destination folder: {save_dir}",
    }, 200
