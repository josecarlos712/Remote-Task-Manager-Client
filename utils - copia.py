from flask import Flask, jsonify, request
import requests
import threading
from flask_cors import CORS
from waitress import serve
import multiprocessing

import commands


class RemoteClient:
    def __init__(self, name, port, target_url):
        """
        Initialize the RemoteClient with a name, port for its server, and the target URL of the other peer.

        Args:
            name (str): A unique name for this instance of RemoteClient (e.g., 'Point A').
            port (int): The port on which this client will run its WSGI server.
            target_url (str): The URL of the other client (e.g., 'http://localhost:5001').
        """
        self.name = name
        self.app = Flask(__name__)
        self.port = port
        self.target_url = target_url

        # Enable CORS for all routes, or specify allowed origins
        CORS(self.app, resources={r"/api/*": {"origins": "*", "methods": ["OPTIONS", "POST"]}})

        # Register routes
        APIRoute(self.app, 'test', test)  # Default method--POST
        APIRoute(self.app, 'command', command)  # Default method--POST

        # Initialize commands
        commands.setup()

    def send_request(self, data):
        """
        Send a POST request with a JSON payload to the target URL.

        Args:
            data (dict): The JSON data to send in the request.
        """
        try:
            response = requests.post(f'{self.target_url}/receive', json=data)
            print(f"{self.name} sent request. Response from target:", response.json())
        except Exception as e:
            print(f"{self.name} failed to send request: {e}")

    def start_server(self):
        """
        Start the Waitress WSGI server in a separate thread.
        """
        def run_server():
            serve(
                self.app,
                host='0.0.0.0',
                port=self.port,
                threads=multiprocessing.cpu_count() * 2,  # Recommended thread count
                channel_timeout=300  # 5-minute timeout
            )

        # Start server in a separate thread
        threading.Thread(target=run_server, daemon=True).start()


class APIRoute:
    GET = "GET"
    POST = "POST"

    def __init__(self, app, route, action, method=POST):
        self.app = app
        self.route = route
        self.action = action
        self.method = method

        # Define a unique endpoint function dynamically
        def endpoint():
            json_data = request.get_json()  # Extract JSON body
            return action(json_data)  # Pass JSON data to the action

        # Use the route name as the endpoint function name to avoid naming conflicts
        try:
            app.add_url_rule(f'/api/{route}', endpoint=route, view_func=endpoint, methods=[method])
        except Exception as e:
            print(f"Failed creating the endpoint: {e}")


def test(json_data):
    return jsonify({"status": "online", "message": f"APIRest is running!"}), 200


def command(json_data):
    # Check if 'command' is in json_data
    if 'command' in json_data:
        # Get the command from the dictionary
        command_name = json_data['command']

        # Check if the command exists in commands.commands
        if command_name in commands.commands:
            command_instance = commands.commands[command_name]

            # Check if 'message' is in json_data and execute accordingly
            if 'message' in json_data:
                command_instance.execute(message=json_data['message'])
                return jsonify({
                    "status": "success",
                    "message": f"Command {command_name} executed with message \"{json_data['message']}\"."
                }), 200
            else:
                command_instance.execute()
                return jsonify({
                    "status": "success",
                    "message": f"Command {command_name} executed."
                }), 200
        else:
            # Command exists, but it's not valid in commands.commands
            return jsonify({
                "status": "failed",
                "message": f"Command '{command_name}' does not exist in the available commands."
            }), 404

    else:
        # If 'command' is not in json_data
        return jsonify({
            "status": "failed",
            "message": "Command not provided."
        }), 400
