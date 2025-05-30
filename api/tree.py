import logging
from typing import Any, Dict

from flask import jsonify, current_app, Response
from utils.APIResponse import error_handler
from utils import APIResponse


def register(app, path) -> tuple[str, int]:
    methods = ['GET']

    app.add_url_rule(
        f'/{path}',
        endpoint=path,
        view_func=error_handler(handler),
        methods=methods
    )

    return "API endpoint registered successfully", 200


def handler(args: Dict[str, Any]) -> Response:
    """
    Returns the API structure in JSON format.
    """
    api_tree = build_api_tree()
    logging.info(f"API tree depth: {args.get('depth', 'not specified')}")
    return APIResponse.SuccessResponse("This is a success response", api_tree).to_response()


def build_api_tree():
    """
    Generates a hierarchical tree of API routes using Flask's url_map.
    - Excludes dynamic routes (e.g., <path:filename>)
    - Includes allowed HTTP methods per endpoint
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
