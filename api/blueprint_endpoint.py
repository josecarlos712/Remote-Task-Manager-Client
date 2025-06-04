# Blueprint for modular API routes
from pathlib import Path
from typing import Dict, Any

from flask import jsonify, Response

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse


def register(endpoint_loader, app, path) -> tuple[str, int]:
    """
    Registers the API endpoint with a Flask application.
    Functionality:
    - Registers a new API endpoint using Flask's add_url_rule
    - Implements error handling using the error_handler decorator
    - Ensures only endpoint.py can register new endpoints


    :param: app: Flask: Flask application instance
    :param: path: str: The path for the endpoint being registered

    :returns: tuple[str, int]: (Message, HTTP status code)
    """
    # Define HTTP methods supported by this endpoint
    methods = ['GET']

    # Register the API endpoint with Flask
    app.add_url_rule(
        f'/{path}',  # The actual URL path
        endpoint=path,  # Unique endpoint identifier
        view_func=error_handler(handler),  # Wrap handler with error handling
        methods=methods  # Supported HTTP methods
    )

    # Special case: Only the endpoint.py file can dynamically register new endpoints
    if Path(__file__).name == "endpoint.py":
        # Load endpoints recursively from the specified path
        response, code = endpoint_loader.load_endpoints(app, relative_path=path)
        return response, code

    # Successful import
    return "API endpoint registered successfully", 200


def handler(args: Dict[str, Any]) -> Response:
    """
        Main handler function for API endpoint.

        Parameters:
            args (Dict[str, Any]): Request arguments and data

        Returns:
            Response: Flask response object

        Implementation Notes:
        - This function should be implemented to handle actual business logic
        - Must return a response using the APIResponse module and the method to_response()
        - Example return: APIResponse.SuccessResponse("message", data).to_response()
        - For errors: APIResponse.ErrorResponse("error message", code).to_response()
        """
    ...
    # TODO: Implement actual endpoint logic here
    # Use APIResponse module for returning responses or errors.
    #   return APIResponse.SuccessResponse("This is a success response").to_response()
