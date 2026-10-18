# -*- coding: utf-8 -*-
"""GET/POST download list/status/remove/clear - download job progress."""
from flask import jsonify, request

from auth import require_api_key
from command_modules import download_file as df
from config import logger
from utils.APIResponse import ErrorResponse


def _ok(message, data):
    # Avoid SuccessResponse INFO spam: this endpoint is polled frequently.
    n = len((data or {}).get("downloads") or []) if isinstance(data, dict) else "-"
    logger.debug("download_status: %s (%s)", message, n)
    return jsonify({"status": "success", "message": message, "data": data}), 200


def download_list():
    active_only = False
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        active_only = bool(body.get("active_only"))
    else:
        active_only = request.args.get("active_only", "").lower() in ("1", "true", "yes")
    jobs = df.list_downloads(active_only=active_only)
    return _ok("Download list", {"downloads": jobs})


def download_status():
    job_id = None
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        job_id = body.get("job_id")
    else:
        job_id = request.args.get("job_id")
    if not job_id:
        return jsonify(ErrorResponse("Missing job_id").to_dict()), 400
    job = df.get_download(str(job_id))
    if not job:
        return jsonify(ErrorResponse("Download job not found").to_dict()), 404
    return _ok("Download status", job)


def download_remove():
    body = request.get_json(silent=True) or {}
    job_id = body.get("job_id")
    ok, message = df.remove_download(job_id)
    if not ok:
        code = 404 if "not found" in message.lower() else 400
        return jsonify(ErrorResponse(message).to_dict()), code
    return _ok(message, {"job_id": str(job_id), "removed": True})


def download_clear_finished():
    removed = df.clear_finished_downloads()
    return _ok("Cleared finished downloads", {"removed": removed})


def download_cancel():
    body = request.get_json(silent=True) or {}
    job_id = body.get("job_id")
    ok, message = df.cancel_download(job_id)
    if not ok:
        code = 404 if "not found" in message.lower() else 400
        return jsonify(ErrorResponse(message).to_dict()), code
    return _ok(message, {"job_id": str(job_id), "cancelled": True})


def register(app, module_name):
    app.add_url_rule(
        "/api/download/list",
        endpoint="download_list",
        view_func=require_api_key(download_list),
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/api/download/status",
        endpoint="download_status",
        view_func=require_api_key(download_status),
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/api/download/remove",
        endpoint="download_remove",
        view_func=require_api_key(download_remove),
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/download/clear_finished",
        endpoint="download_clear_finished",
        view_func=require_api_key(download_clear_finished),
        methods=["POST"],
    )
    app.add_url_rule(
        "/api/download/cancel",
        endpoint="download_cancel",
        view_func=require_api_key(download_cancel),
        methods=["POST"],
    )
    return 0
