"""API key authentication helpers for the Flask agent."""
from functools import wraps

from flask import request, jsonify

import config
from config import logger
from utils.APIResponse import ErrorResponse


def require_api_key(f):
    """Require X-Client-API-Key header matching the configured agent key."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        expected = config.get_api_key()
        provided = request.headers.get("X-Client-API-Key") or ""
        if not expected:
            logger.error("API key not configured on client; rejecting protected request.")
            return jsonify(
                ErrorResponse("Client API key not configured", config.LogLevel.ERROR).to_dict()
            ), 503
        if provided != expected:
            logger.warning("Rejected request with invalid X-Client-API-Key.")
            return jsonify(
                ErrorResponse("Invalid or missing API key", config.LogLevel.WARNING).to_dict()
            ), 401
        return f(*args, **kwargs)

    return wrapper
