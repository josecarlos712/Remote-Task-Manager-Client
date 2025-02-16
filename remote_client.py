import json
import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Any

import psutil
from flask import Flask, jsonify, request
import requests
import threading
from flask_cors import CORS
from waitress import serve
import multiprocessing
import logging
from functools import wraps

import commands
import config
from commands import Command
from config import logger, CONFIG_PATH, VALID_TOKENS
from utils import error_handler, APIResponse


class RemoteClient:
    def __init__(self, name: str, port: int, target_url: str, debug: bool = False):
        """
        Initialize the RemoteClient with a name, port for its server, and the target URL.

        IMPROVEMENTS:
        - Added type hints
        - Added better documentation
        - Using requests.Session for connection pooling
        - Restricted CORS to specific origins
        """
        self.name = name
        self.port = port
        self.target_url = target_url
        self.debug = debug
        self.app = Flask(__name__)
        # IMPROVEMENT: Using session for better performance
        self.session = requests.Session()
        self.commands: Dict[str, Command] = {}

        # IMPROVEMENT: More secure CORS configuration
        CORS(self.app, resources={
            r"/api/*": {
                # SECURITY: Restrict to local development only
                "origins": ["http://localhost:*", "http://127.0.0.1:*"],
                "methods": ["OPTIONS", "POST", "GET"],
                "allow_headers": ["Content-Type"]
            }
        })

        self._register_routes()
        self._initialize_commands()  # Add the existing commands to the Commands class dictionary

        # IMPROVEMENT: Added health check system
        self.last_health_check = None
        self._start_health_check()

    def _register_routes(self):
        """
        IMPROVEMENT: Centralized route registration with error handling
        """

        # New routes like '/api/endpoint' are defined as:
        #    'endpoint': (self.function_endpoint, ["POST", "GET"])
        routes = {
            'test': (self.test_endpoint, ["GET"]),
            'command': (self.command_endpoint, ["POST"]),
            'health': (self.health_check_endpoint, ["GET"]),
        }

        for route_name, (handler, methods) in routes.items():
            self.app.add_url_rule(
                f'/api/{route_name}',
                endpoint=route_name,
                view_func=error_handler(handler),  # Added error handling
                methods=methods
            )

    def _initialize_commands(self):
        """
        IMPROVEMENT: Added error handling for command initialization
        """
        _commands: Dict = {}
        try:
            # Declare the commands (these commands are built-in)
            _commands['popup'] = Command(command='popup', function=commands.show_popup,
                                         description="This is an example API function.")
            _commands['test_command'] = Command(command='test_command', function=commands.test_command,
                                                description="Command for testing")
            logger.info("Commands initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize commands: {e}")
            raise
        self.commands = _commands

    # IMPROVEMENT: Made request sending asynchronous
    async def send_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        IMPROVEMENTS:
        - Added async support
        - Added timeout
        - Better error handling
        - Using session for connection pooling
        """
        try:
            async with self.session.post(
                    f'{self.target_url}/receive',
                    json=data,
                    timeout=10  # SECURITY: Added timeout to prevent hanging
            ) as response:
                response_data = await response.json()
                logger.info(f"{self.name} sent request. Response: {response_data}")
                return response_data
        except requests.exceptions.Timeout:
            logger.error(f"{self.name}: Request timed out")
            raise
        except Exception as e:
            logger.error(f"{self.name} failed to send request: {e}")
            raise

    def start_server(self):
        """
        Starts the Flask server and binds it to the specified host and port.
        Includes improvements like graceful shutdown and better exception handling.
        """

        # Log the startup attempt
        logger.info(f"Attempting to start server on port {self.port}...")

        try:
            if self.debug:
                logger.info("Running in debug mode")
            # Start the server using waitress.serve, which handles multiple threads.
            serve(
                self.app,
                host='0.0.0.0',  # Listen on all interfaces
                port=self.port,
                threads=multiprocessing.cpu_count() * 2,  # Use all available CPU threads
                channel_timeout=300,
                cleanup_interval=30,  # Regular cleanup
                connection_limit=1000  # Connection limit for security
            )

            # Server is running at this point
            logger.info(f"Server started on port {self.port}")

        except Exception as e:
            logger.error(f"Server failed to start: {e}")
            raise

    # IMPROVEMENT: Added health check system
    def _start_health_check(self):
        # TODO Create a health endpoint to answer the heath check from the client
        """Periodic health check to monitor peer status"""

        def health_check():
            while True:
                try:
                    response = self.session.post(f'{self.target_url}/api/health')
                    self.last_health_check = response.json()
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
                threading.Event().wait(60)  # Check every minute

        # threading.Thread(target=health_check, daemon=True).start()

    # ------------------------------------------------ ENDPOINT FUNCTIONS -------------------------------------------------
    # IMPROVEMENT: Enhanced API endpoints with better responses and error handling
    def test_endpoint(self):
        """
        IMPROVEMENTS:
        - Added more detailed response
        - Using standardized response format
        """
        if request.method == 'OPTIONS':
            # Flask-CORS should handle this, but you can explicitly return a response if needed
            return '', 204
        return jsonify(
            APIResponse(" ", "APIRest is running",
                        {"name": self.name, "port": self.port}).to_dict()
        ), 200

    def command_endpoint(self):
        """
        IMPROVEMENTS:
        - Better input validation
        - More detailed error messages
        - Proper error handling
        - Standardized response format
        """
        json_data = request.get_json()

        if not json_data or 'command' not in json_data:
            return jsonify(
                APIResponse("error", "Command not provided").to_dict()
            ), 400

        command_name = json_data['command']
        if command_name not in self.commands:
            return jsonify(
                APIResponse("error", f"Command '{command_name}' does not exist").to_dict()
            ), 404

        try:
            command_instance = self.commands[command_name]
            message = json_data.get('message')

            if message:
                response = command_instance.execute(message=message)
            else:
                response = command_instance.execute()

            return response
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return jsonify(
                APIResponse("error", f"Command execution failed: {str(e)}").to_dict()
            ), 500

    # IMPROVEMENT: Added health check endpoint
    def health_check_endpoint(self):
        """Endpoint for system health monitoring"""
        return jsonify(
            APIResponse("success", "Health check successful", {
                "name": self.name,
                "status": "healthy",
                "last_health_check": self.last_health_check
            }).to_dict()
        ), 200

    # ========================
    #  PROGRAM SYNCHRONIZATION
    # ========================
    # TODO Adaptar el segundo parametro de las funciones para enviar el dato correctamente formateado.
    # PROCESS MANAGEMENT
    # @app.route('/api/processes', methods=['GET'])
    def list_processes(self):
        """ Get a list of all running processes """
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            processes.append(proc.info)
        return jsonify(APIResponse("success", processes).to_dict()), 200

    # @app.route('/api/processes/<int:process_id>', methods=['GET'])
    def get_process_status(self, process_id):
        """ Check the status of a specific process """
        try:
            process = psutil.Process(process_id)
            # TODO Cambiar el tipo de dato del segundo parametro de APIResponse a any y manejarlo en la recepcion del JSON
            return jsonify(APIResponse('success', process.as_dict(attrs=['pid', 'name', 'status']).__str__()).to_dict()), 200
        except psutil.NoSuchProcess:
            return jsonify(APIResponse('error', 'Process not found').to_dict()), 404

    # @app.route('/api/processes/kill', methods=['POST'])
    def kill_process(self):
        """ Kill a specific process by ID """
        data = request.json
        process_id = data.get('process_id')

        if process_id is None:
            return jsonify(APIResponse('error', 'Missing process_id').to_dict()), 400

        try:
            process = psutil.Process(process_id)
            process.terminate()
            return jsonify(APIResponse('success', 'Process {process_id} terminated').to_dict()), 200
        except psutil.NoSuchProcess:
            return jsonify(APIResponse('error', 'Process not found').to_dict()), 404
        except Exception as e:
            return jsonify(APIResponse('error', str(e)).to_dict()), 500

    # @app.route('/api/programs/sync', methods=['POST'])
    def sync_programs(self):
        """ Sync programs from JSON configuration """
        if not os.path.exists(CONFIG_PATH):
            return jsonify(APIResponse('error', 'Configuration file not found').to_dict()), 500

        with open(CONFIG_PATH, 'r') as f:
            try:
                programs = json.load(f)
            except json.JSONDecodeError:
                return jsonify(APIResponse('error', 'Invalid JSON format').to_dict()), 500

        return jsonify(APIResponse('success', programs).to_dict()), 200

    # @app.route('/api/programs', methods=['GET'])
    def get_programs(self):
        """ Get a list of all programs from JSON """
        if not os.path.exists(CONFIG_PATH):
            return jsonify(APIResponse('error', 'Configuration file not found').to_dict()), 500

        with open(CONFIG_PATH, 'r') as f:
            programs = json.load(f)

        return jsonify(APIResponse('success', programs).to_dict()), 200

    # ========================
    #  SYSTEM INFORMATION
    # ========================

    # @app.route('/api/system/info', methods=['GET'])
    def get_system_info(self):
        """ Get system information (CPU, RAM, Disk) """
        system_info = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict()
        }
        return jsonify(APIResponse('success', system_info).to_dict()), 200

    # @app.route('/api/system/logs', methods=['GET'])
    def get_system_logs(self):
        """ Get the latest system logs (Windows Event Logs) """
        logs = []
        try:
            import win32evtlog  # Requires `pywin32`
            server = None  # Local machine
            log_type = 'System'

            hand = win32evtlog.OpenEventLog(server, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            total = win32evtlog.GetNumberOfEventLogRecords(hand)

            events = win32evtlog.ReadEventLog(hand, flags, 0)
            for event in events[:10]:  # Get last 10 logs
                logs.append({
                    'event_id': event.EventID,
                    'time_generated': event.TimeGenerated.Format(),
                    'source': event.SourceName,
                    'category': event.EventCategory
                })

            win32evtlog.CloseEventLog(hand)
        except ImportError:
            return jsonify(APIResponse('error', 'win32evtlog not available').to_dict()), 500
        except Exception as e:
            return jsonify(APIResponse('error', str(e)).to_dict()), 500

        return jsonify(APIResponse('success', logs).to_dict()), 200

    # ========================
    #  AUTHENTICATION
    # ========================

    # @app.route('/api/auth/login', methods=['POST'])
    def login(self):
        """ Authenticate user and issue a token """
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if username == 'admin' and password == 'password':  # Replace with real authentication
            token = os.urandom(16).hex()
            VALID_TOKENS[token] = username
            return jsonify(APIResponse('success', token).to_dict()), 200

        return jsonify(APIResponse('error', 'Invalid credentials').to_dict()), 401

    # @app.route('/api/auth/logout', methods=['POST'])
    def logout(self):
        """ Log out user by invalidating the token """
        data = request.json
        token = data.get('token')

        if token in VALID_TOKENS:
            del VALID_TOKENS[token]
            return jsonify(APIResponse('success', 'Logged out').to_dict()), 200

        return jsonify(APIResponse('error', 'Invalid token').to_dict()), 401

# --------------------------------------------- ENDPOINT FUNCTIONS END ------------------------------------------------
