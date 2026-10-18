# -*- coding: utf-8 -*-
"""GET/POST /api/program/list - serve config/programs.json."""
import json
from pathlib import Path

from flask import jsonify

import config
from auth import require_api_key
from utils.APIResponse import SuccessResponse, ErrorResponse


def _programs_path() -> Path:
    configured = config.get_setting("path_programs", "config/programs.json") or "config/programs.json"
    path = Path(configured)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def program_list():
    path = _programs_path()
    if not path.exists():
        return jsonify(SuccessResponse("No programs file", {}).to_dict()), 200
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return jsonify(ErrorResponse(f"Could not read programs.json: {e}", config.LogLevel.ERROR).to_dict()), 500

    # Normalize to dict keyed by name for Django sync helpers
    if isinstance(data, list):
        as_dict = {item.get("name") or f"program_{i}": item for i, item in enumerate(data)}
    elif isinstance(data, dict):
        as_dict = data
    else:
        as_dict = {}
    return jsonify(SuccessResponse("Program list", as_dict).to_dict()), 200


def register(app, module_name):
    app.add_url_rule(
        "/api/program/list",
        endpoint="program_list",
        view_func=require_api_key(program_list),
        methods=["GET", "POST"],
    )
    return 0
