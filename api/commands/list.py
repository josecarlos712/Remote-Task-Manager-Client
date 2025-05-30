# Blueprint for modular API routes
from pathlib import Path
from typing import Dict, Any

from flask import jsonify, Response

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse
from utils.endpoints_loader import load_endpoints


def register(app, path) -> tuple[str, int]:
    """
    Registers the API endpoint with the Flask application.
    :param app: Flask application instance
    :param path: The path for the endpoint to be registered
    :return: Tuple containing a message and HTTP status code
    """
    methods = ['GET']

    app.add_url_rule(
        f'/{path}',
        endpoint=path,
        view_func=error_handler(handler),  # Added error handling
        methods=methods
    )

    # Successful import
    return "API endpoint registered successfully", 200


def handler(args: Dict[str, Any]) -> Response:
    # Here goes the function to implement
    ...
    # Use APIResponse module for returning responses or errors.
    #   return APIResponse.SuccessResponse("This is a success response").to_response()
