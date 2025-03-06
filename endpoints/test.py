# Blueprint for modular API routes
from flask import jsonify, request

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse


def register(app, path) -> int:
    methods = ['GET']

    app.add_url_rule(
        f'/api/{path}',
        endpoint=path,
        view_func=error_handler(handler),  # Added error handling
        methods=methods
    )

    #Successful import
    return 0


def handler() -> APIResponse:
    #Here goes the function to implement
    if request.method == 'OPTIONS':
        # Flask-CORS should handle this, but you can explicitly return a response if needed
        return '', 204
    return jsonify(
        APIResponse.SuccessResponse("APIRest is running",
                                    {"name": self.name, "port": self.port}).to_dict()
    ), 200
    # Use APIResponse module for returning responses or errors.
    #   return jsonify(APIResponse.SuccessResponse("This is a success response").to_dict()), 200
