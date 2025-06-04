# Blueprint for modular API routes
from pathlib import Path

from flask import jsonify, Response

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse


def register(app, path) -> tuple[str, int]:
    """
    Registers the API endpoint with the Flask application.
    :param app: Flask application instance
    :param path: The path for the endpoint to be registered
    :return: tuple[str, int]: Tuple containing a message and HTTP status code
    """
    methods = ['POST']

    app.add_url_rule(
        f'/{path}',
        endpoint=path,
        view_func=error_handler(handler),  # Added error handling
        methods=methods
    )

    # Successful import
    return "API endpoint registered successfully", 200


def handler(args: Dict[str, Any]) -> Response:
    # Execute the command handler.
    ...
    # Use APIResponse module for returning responses or errors.
    return APIResponse.SuccessResponse("This is a success response").to_response()
