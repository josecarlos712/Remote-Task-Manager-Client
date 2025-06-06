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
    methods = ['POST']

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
        response, code = endpoint_loader.load_endpoints(path)
        return response, code

    # Successful import
    return f"{__file__} - API endpoint registered successfully", 200


def handler(**kwargs: Dict[str, Any]) -> Response:
    # **kargs: Dict[str, Any]: Contains the name of the command and any additional parameters.
    # {
    #     'command' (str): 'YOUR_COMMAND_NAME',
    #     # params from the request body (json)
    #     'param1': 'value1',
    #     'param2': 'value2',
    #     }
    # }

    # Imports inside the function to avoid circular or premature imports.
    from config.config import SERVER_SOCKET
    from remote_client import RemoteClient
    # Get the command specified in the request arguments.
    server_socket: RemoteClient = SERVER_SOCKET
    if 'command' not in kwargs:
        return APIResponse.ErrorResponse("Command name is required", 400).to_response()

    # Call the commands loader with the provided arguments.
    response = SERVER_SOCKET.commands_loader(**kwargs)
    # Use APIResponse module for returning responses or errors.
    return response
