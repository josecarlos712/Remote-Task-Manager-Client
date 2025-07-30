import logging
from typing import Any, Dict

from flask import jsonify, current_app, Response
from utils.APIResponse import error_handler
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
        response, code = endpoint_loader.load_endpoints(path)
        return response, code

    # Successful import
    return f"{__file__} - API endpoint registered successfully", 200


def handler(depth) -> Response:
    """
    Returns the API structure in JSON format.
    """
    api_tree = build_api_tree()

    if not depth:
        logging.info(f"API tree depth: {depth if not depth else 'not specified'}")
    return APIResponse.SuccessResponse("This is a success response", api_tree).to_response()


def build_api_tree() -> Dict[str, Any]:
    """
    Generates a hierarchical tree of API routes using Flask's url_map.
    - Excludes dynamic routes (e.g., <path:filename>)
    - Includes allowed HTTP methods per endpoint
    - Returns a nested dictionary structure representing the API endpoints in the format:
    {
        "endpoint1": {
            "sub_endpoint1": {
                "_methods": ["GET", "POST"]
            },
            "sub_endpoint2": {
                "_methods": ["GET"]
            }
        },
        "endpoint2": {
            "_methods": ["GET", "PUT"]
        }
    }
    """
    tree = {}

    for rule in current_app.url_map.iter_rules():
        # Exclude dynamic routes (those containing <...>)
        if "<" in rule.rule:
            continue

        parts = rule.rule.strip('/').split('/')
        node = tree

        for part in parts:
            if part not in node:
                node[part] = {}

            node = node[part]

        # Add the allowed methods for this endpoint (excluding default OPTIONS/HEAD)
        node["_methods"] = sorted(method for method in rule.methods if method not in {"OPTIONS", "HEAD"})

    return tree
