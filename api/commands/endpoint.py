# Blueprint for modular API routes
from pathlib import Path

from flask import jsonify

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse
from utils.endpoints_loader import load_endpoints


def register(app, path) -> tuple[str, int]:
    """Registers the API endpoint with the Flask application.
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

    # Only the endpoint.py file can register new endpoints
    if Path(__file__).name == "endpoint.py":
        response, code = load_endpoints(app, relative_path=path)
        return response, code

    #Successful import
    return f"Something went wrong registering API endpoint '{path}'", 500


def handler() -> APIResponse:
    #Here goes the function to implement
    ...
    # Use APIResponse module for returning responses or errors.
    #   return jsonify(APIResponse.SuccessResponse("This is a success response").to_dict()), 200
