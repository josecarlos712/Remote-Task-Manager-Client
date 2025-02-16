# IMPROVEMENT: Added type hints and essential imports
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Any
from flask import Flask, jsonify, request
import requests
import threading
from flask_cors import CORS
from waitress import serve
import multiprocessing
from functools import wraps
from config import logger


# IMPROVEMENT: Added standardized API response structure using dataclass
@dataclass
class APIResponse:
    """Standardized API response structure for consistent response format"""
    status: str
    message: str
    data: Optional[Dict] = None

    def to_dict(self) -> dict:
        response = {"status": self.status, "message": self.message}
        if self.data:
            response["data"] = self.data
        return response


# IMPROVEMENT: Added error handling decorator
def error_handler(f):
    """
    Decorator that wraps API endpoints with standardized error handling.
    Catches exceptions and returns appropriate error responses.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify(
                APIResponse("error", f"Internal server error: {str(e)}").to_dict()
            ), 500

    return wrapper
