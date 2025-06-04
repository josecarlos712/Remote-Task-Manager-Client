# Blueprint for modular API routes
from pathlib import Path
from typing import Dict, Any

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
    SERVER_SOCKET.commands_loader(**kwargs)
    # Use APIResponse module for returning responses or errors.
    return APIResponse.SuccessResponse("This is a success response").to_response()
