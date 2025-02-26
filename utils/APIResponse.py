import logging
from functools import wraps
from typing import Optional, Dict

import psutil
from flask import jsonify

from config import LogLevel, logger


class APIResponse:
    """Base API Response class for standardizing API responses."""

    def __init__(self, status: str, message: str, data: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.data = data

    def to_dict(self) -> dict:
        response = {"status": self.status, "message": self.message}
        if self.data is not None:
            response["data"] = self.data
        return response


# ========================
# SUCCESS RESPONSES
# ========================

class SuccessResponse(APIResponse):
    """Base class for all successful responses."""

    def __init__(self, message: str, data: Optional[Dict] = None):
        # Log successful response with message and data details
        logging.log(LogLevel.INFO.value, f"SuccessResponse: {message}, Data: {data}")
        super().__init__("success", message, data)


class ProcessResponse(SuccessResponse):
    """Response class for process-related operations."""

    def __init__(self, processes: list[psutil.Process], message: Optional[str]):
        # Log process-related response with number of processes
        logging.log(LogLevel.INFO.value, f"ProcessResponse: {len(processes)} processes retrieved.")
        super().__init__(message if message else "Process operation successful", {"processes": processes})


class ProgramResponse(SuccessResponse):
    """Response class for program sync & retrieval."""

    def __init__(self, programs: Dict):
        # Log program retrieval success with program count
        logging.log(LogLevel.INFO.value, f"ProgramResponse: {len(programs)} programs retrieved.")
        super().__init__("Program operation successful", {"programs": programs})


class SystemInfoResponse(SuccessResponse):
    """Response class for system information requests."""

    def __init__(self, system_data: Dict, message: Optional[str] = None):
        # Log system info retrieval success
        logging.log(LogLevel.INFO.value, f"SystemInfoResponse: {message or 'System info retrieved'}")
        super().__init__("System information", system_data)


class LogResponse(SuccessResponse):
    """Response class for system logs."""

    def __init__(self, logs: Dict):
        # Log number of logs retrieved
        logging.log(LogLevel.INFO.value, f"LogResponse: {len(logs)} log entries retrieved.")
        super().__init__("System logs retrieved", {"logs": logs})


# ========================
# ERROR RESPONSES
# ========================

class ErrorResponse(APIResponse):
    """Base class for all error responses."""

    def __init__(self, message: str, log_level: LogLevel):
        # Log error response with severity level
        logging.log(log_level.value, f"ErrorResponse: {message}")
        super().__init__("error", message)


class NotFoundResponse(ErrorResponse):
    """Response class for resource not found errors."""

    def __init__(self, resource: str):
        # Log missing resource
        logging.log(LogLevel.WARNING.value, f"NotFoundResponse: {resource} not found.")
        super().__init__(f"{resource} not found", LogLevel.WARNING)


class ValidationErrorResponse(ErrorResponse):
    """Response class for validation errors (e.g., missing parameters)."""

    def __init__(self, field: str):
        # Log missing or invalid field
        logging.log(LogLevel.WARNING.value, f"ValidationErrorResponse: Missing or invalid field: {field}")
        super().__init__(f"Missing or invalid field: {field}", LogLevel.WARNING)


class InternalErrorResponse(ErrorResponse):
    """Response class for unexpected internal errors."""

    def __init__(self, error: str):
        # Log internal server error
        logging.log(LogLevel.ERROR.value, f"InternalErrorResponse: {error}")
        super().__init__(f"Internal server error: {error}", LogLevel.ERROR)


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
            logger.error(LogLevel.ERROR.value, f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify(
                ErrorResponse(f"Internal server error: {str(e)}", log_level=LogLevel.ERROR).to_dict()
            ), 500

    return wrapper
