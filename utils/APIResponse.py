import json
import logging
from functools import wraps
from typing import Optional, Dict, Any

import psutil

import logging
from flask import jsonify, Response, request

logger = logging.getLogger(__name__)


class APIResponse():
    """Base API Response class for standardizing API responses."""

    def __init__(self, status: str, message: str, code: int, data: Optional[Any] = None):
        self.status = status
        self.message = message
        self.data = data
        self.code = code

    def to_dict(self) -> dict:

        if isinstance(self, ErrorResponse):
            response = {"status": self.status, "error": self.message}
        else:
            response = {"status": self.status, "message": self.message}
        if self.data is not None:
            response["data"] = self.data
        return response

    def to_response(self) -> Response:  # Or jsonify
        """
        Converts the API response to a Flask Response object with JSON content.
        """
        # jsonify automatically sets Content-Type to application/json and handles serialization
        # return jsonify(self.to_dict()), self.code # This is simpler if you always return dicts

        # For more explicit control, use Response
        json_string = json.dumps(self.to_dict())
        return Response(json_string, status=self.code, mimetype='application/json')


# ========================
# SUCCESS RESPONSES
# ========================

class SuccessResponse(APIResponse):
    """Base class for all successful responses."""

    def __init__(self, message: str, data: Optional[Any] = None):
        # Log successful response with message and data details
        logging.info(f"SuccessResponse: {message}, Data: {data}")
        if data is None:
            data = {}
        super().__init__("success", message, 200, data)


class ProcessResponse(SuccessResponse):
    """Response class for process-related operations."""

    def __init__(self, processes: list[psutil.Process], message: Optional[str]):
        # Log process-related response with number of processes
        logging.info(f"ProcessResponse: {len(processes)} processes retrieved.")
        super().__init__(message if message else "Process operation successful", {"processes": processes})


class ProgramResponse(SuccessResponse):
    """Response class for program sync & retrieval."""

    def __init__(self, programs: Dict):
        # Log program retrieval success with program count
        logging.info(f"ProgramResponse: {len(programs)} programs retrieved.")
        super().__init__("Program operation successful", {"programs": programs})


class SystemInfoResponse(SuccessResponse):
    """Response class for system information requests."""

    def __init__(self, system_data: Dict, message: Optional[str] = None):
        # Log system info retrieval success
        logging.info(f"SystemInfoResponse: {message or 'System info retrieved'}")
        super().__init__("System information", system_data)


class LogResponse(SuccessResponse):
    """Response class for system logs."""

    def __init__(self, logs: Dict):
        # Log number of logs retrieved
        logging.info(f"LogResponse: {len(logs)} log entries retrieved.")
        super().__init__("System logs retrieved", {"logs": logs})


# ========================
# ERROR RESPONSES
# ========================

class ErrorResponse(APIResponse):
    """Base class for all error responses."""

    def __init__(self, message: str, code: int = 500):
        # Log error response with severity level
        logging.error(f"ErrorResponse: {message}")
        super().__init__("error", message, code)


class NotFoundResponse(ErrorResponse):
    """Response class for resource not found errors."""

    def __init__(self, resource: str):
        # Log missing resource
        logging.warning(f"NotFoundResponse: {resource} not found.")
        super().__init__(f"{resource} not found", 404)


class ValidationErrorResponse(ErrorResponse):
    """Response class for validation errors (e.g., missing parameters)."""

    def __init__(self, field: str):
        # Log missing or invalid field
        logging.warning(f"ValidationErrorResponse: Missing or invalid field: {field}")
        super().__init__(f"Missing or invalid field: {field}", 400)


class InternalErrorResponse(ErrorResponse):
    """Response class for unexpected internal errors."""

    def __init__(self, error: str):
        # Log internal server error
        logging.error(f"InternalErrorResponse: {error}")
        super().__init__(f"Internal server error: {error}", 500)


class BadRequestResponse(ErrorResponse):
    """Response class for bad request errors."""

    def __init__(self, message: str):
        # Log bad request error
        logging.warning(f"BadRequestResponse: {message}")
        super().__init__(f"Bad request: {message}", 400)


class UnauthorizedResponse(ErrorResponse):
    """Response class for unauthorized access errors."""

    def __init__(self, message: str):
        # Log unauthorized access error
        logging.warning(f"UnauthorizedResponse: {message}")
        super().__init__(f"Unauthorized access: {message}", 401)


class ForbiddenErrorResponse(ErrorResponse):
    """Response class for forbidden access errors (authentication succeeded, but user lacks permissions)."""

    def __init__(self, message: str = "Forbidden.", data=None):
        # Log forbidden access error
        logging.warning(f"ForbiddenErrorResponse: {message}")
        # Standard HTTP status code for Forbidden is 403
        super().__init__(message, data)  # Pass message and data to base ErrorResponse
        self.code = 403  # Set the specific HTTP status code


class BadMethodErrorResponse(ErrorResponse):
    """Response class for unsupported HTTP method errors."""

    def __init__(self, method: str, expected_method: str):
        # Log unsupported HTTP method
        logging.warning(f"BadMethodErrorResponse: Unsupported method: {method}")
        super().__init__(f"Unsupported method: {method}. Expected method: {expected_method}", 405)


# IMPROVEMENT: Added error handling decorator
def error_handler(func):
    @wraps(func)  # Important for Flask to properly introspect the view function
    def wrapper(**kwargs):  # Flask will pass URL parameters (like command_id) as keyword arguments here
        try:
            handler_args = kwargs.copy()  # 1. Start with URL Path Parameters

            # Add Query Parameters (if any)
            handler_args.update(request.args.to_dict())

            # Add JSON Body Data (if it's a POST/PUT/PATCH with JSON)
            if request.is_json:  # Checks if Content-Type is application/json
                json_data = request.get_json()  # Parses the JSON body
                if isinstance(json_data, dict):  # Ensure it's a dictionary
                    handler_args.update(json_data)
                # You might add an else here to handle non-dict JSON or log a warning
                # else:
                #     logger.warning(f"Non-dictionary JSON body received for {func.__name__}")

            # Call the actual handler with the consolidated arguments
            return func(**handler_args)

        except Exception as e:
            logger.error(f"{__file__} - Error executing command '{func.__name__}': {e}", exc_info=True)
            # You might want to customize the error response based on the exception type
            return jsonify({"status": "error", "message": str(e)}), 500

    return wrapper


def check_None_API(value, error_message: str = None) -> tuple[Response, int] | tuple[None, int]:
    """
    Check if the given value is None or empty.

    Args:
        value: The value to check.
        error_message (str, optional): An error message to log if the value is None or empty.
    Returns:
        tuple: A tuple containing the API response and an HTTP status code.
    """
    if value is None:
        return BadRequestResponse(error_message).to_response(), 400  # 400 Bad Request
    return None, 200


def check_instance_API(obj, instance, error_message: str = None) -> tuple[Response, int] | tuple[None, int]:
    """

    Returns:
        tuple: A tuple containing the API response and an HTTP status code.
    """
    if obj is isinstance(obj, instance):
        return BadRequestResponse(error_message).to_response(), 400  # 400 Bad Request
    return None, 200
