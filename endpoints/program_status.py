# -*- coding: utf-8 -*-
"""GET /api/program/status - running programs tracked by ProgramExecutor."""
from flask import jsonify

from auth import require_api_key
from commands import ProgramExecutor
from utils.APIResponse import SuccessResponse


def program_status():
    executor = ProgramExecutor.get()
    running = executor.list_running()
    # Map by program_key for Django refresh helpers
    payload = {}
    for item in running:
        key = item.get("program_key") or str(item.get("process_id"))
        payload[key] = {
            "available": True,
            "is_running": True,
            "pid": item.get("pid"),
            "process_id": item.get("process_id"),
            "path": item.get("path"),
        }
    return jsonify(SuccessResponse("Program status", payload).to_dict()), 200


def register(app, module_name):
    app.add_url_rule(
        "/api/program/status",
        endpoint="program_status",
        view_func=require_api_key(program_status),
        methods=["GET", "POST"],
    )
    return 0
