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

import config
from commands.Command import Command
from config.init_config import Configuration
from utils import APIResponse
from utils.APIResponse import ErrorResponse, error_handler
from utils.commands_utils import CommandsLoader

logger = logging.getLogger(__name__)

CONFIG_PATH = 'config/programs.json'


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
        self.commands_loader: CommandsLoader = None
        self.configuration = Configuration()

        # IMPROVEMENT: More secure CORS configuration
        CORS(self.app, resources={
            r"/api/*": {
                # SECURITY: Restrict to local development only
                "origins": ["http://localhost:*", "http://127.0.0.1:*"],
                "methods": ["OPTIONS", "POST", "GET"],
                "allow_headers": ["Content-Type"]
            }
        })

        response, code = self._register_routes()
        if code != 200:
            logger.error(f"Failed to register routes: {response}")
            raise Exception(f"Failed to register routes: {response}")
        logger.info(f"Routes registered successfully")
        self._register_commands()  # Add the existing commands to the Commands class dictionary

        # Health check system
        self.last_health_check = None
        self._start_health_check()

    def _register_routes(self) -> tuple[str, int]:
        """
        IMPROVEMENT: Centralized route registration with error handling
        """
        from utils.endpoints_loader import EndpointsLoader

        # New routes like '/api/endpoint' are defined as:
        #    'endpoint': (self.function_endpoint, ["POST", "GET"])
        routes = {
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

        # Load dynamic routes
        endpoints_loader = EndpointsLoader(app=self.app)
        # First, register the root endpoint. All the other endpoints will be registered recursively.
        response, code = endpoints_loader.load_endpoints(endpoints_loader, 'api')
        # print all the routes
        self.app.logger.info(self.app.url_map)
        return response, code

    def _register_commands(self) -> tuple[str, int]:
        """Load commands from the commands folder."""
        from utils.commands_utils import CommandsLoader
        self.commands_loader = CommandsLoader(self.app)
        response, code = self.commands_loader.discover_commands()
        if code != 200:
            logger.error(f"Failed to load commands: {response}")
            return response, code

        return response, code

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

    def _load_all_commands(self) -> None:
        """
        Discovers and loads all command modules from the 'commands' subdirectory
        and registers them. This ensures they are available in _registered_commands.
        """
        import importlib
        # All the commands are loaded from the 'commands' directory, so we set it as a imported package.
        import commands as command_pkg
        from commands import Command as command_file
        from commands.Command import Command

        commands_dir = os.path.join(os.path.dirname(__file__), 'commands')

        if not os.path.isdir(commands_dir):
            logger.error(f"Commands directory not found at expected path: {commands_dir}")
            _commands_loaded_flag = True  # Mark as loaded to prevent repeated error logs
            return

        logger.info(f"Initiating command loading from: {commands_dir}")

        # Determine the base Python package path for command modules
        # So, the commands within the 'commands' folder would be similar to 'commands.example_command'
        base_package_for_commands = f"commands"

        for filename in os.listdir(commands_dir):
            exclude_files = ['__init__.py', 'Command.py']  # Exclude these files from loading
            if filename.endswith('.py') and filename not in exclude_files:
                module_name = filename[:-3]  # Remove .py extension (e.g., 'list', 'get_time')
                full_module_import_path = f"{base_package_for_commands}.{module_name}"

                try:
                    logger.debug(f"Attempting to import command module: {full_module_import_path}")
                    command_module = importlib.import_module(full_module_import_path)

                    if hasattr(command_module, 'register'):
                        # Call the 'register' function within the individual command module.
                        # It returns (Command_obj, 200) or (error_message, error_code).
                        reg_result, reg_code = command_module.register()

                        if reg_code == 200 and isinstance(reg_result, Command):
                            response, code = command_file.add_command(reg_result)
                            if code != 200:
                                logger.error(f"Failed to add command '{reg_result['name']}': {response}")
                            logger.info(f"Successfully registered command: '{reg_result['name']}' from '{filename}'")
                        else:
                            logger.warning(
                                f"Failed to register command from '{filename}': {reg_result} (Code: {reg_code})")
                    else:
                        logger.warning(f"Command module '{filename}' has no 'register()' function; skipping.")

                except ImportError as ie:
                    logger.error(f"ImportError loading command module '{full_module_import_path}': {ie}")
                except Exception as e:
                    logger.error(f"Error during registration process for '{filename}': {e}", exc_info=True)

        _commands_loaded_flag = True
        response, code = command_file.get_all_commands()
        logger.info(f"Finished loading commands. Total registered: {len(response)}.")

    # ------------------------------------------------ ENDPOINT FUNCTIONS -------------------------------------------------
    # IMPROVEMENT: Enhanced API api with better responses and error handling
    def command_endpoint(self):
        """
        Endpoint to execute a command.

        IMPROVEMENTS:
        - Structured error handling with appropriate log levels.
        - Clearer response messages.
        - Separation of concerns: JSON validation and command execution are separate functions.
        """
        json_data = request.get_json()

        # Validate that JSON data exists and contains 'command'
        if not json_data or 'command' not in json_data:
            logging.log(config.LogLevel.ERROR.value, "CommandEndpoint: Missing 'command' in request.")
            return jsonify(ErrorResponse("Command not provided").to_dict()), 400

        command_name = json_data['command']

        # Validate that command exists
        if command_name not in self.commands:
            logging.log(config.LogLevel.ERROR.value, f"CommandEndpoint: Command '{command_name}' does not exist.")
            return jsonify(
                ErrorResponse(f"Command '{command_name}' does not exist").to_dict()), 404

        command = self.commands.get(command_name)

        message = json_data.get('message')
        if command.needs_message() and not message:
            logging.log(config.LogLevel.ERROR.value, f"CommandEndpoint: Command '{command_name}' needs a message.")
            return jsonify(
                ErrorResponse(f"Command '{command_name}' needs a message.").to_dict()), 400

        try:
            return command.execute(message)
        except Exception as e:
            logging.log(config.LogLevel.ERROR.value,
                        f"CommandEndpoint: Execution failed for command '{command_name}': {e}")
            return jsonify(ErrorResponse(f"Command execution failed: {str(e)}").to_dict()), 500

    # IMPROVEMENT: Added health check endpoint
    def health_check_endpoint(self):
        """Endpoint for system health monitoring"""
        # This endpoint checks the all the PC instant values (those which can be obtained inmediately) and refresh the internal variables
        # To refresh more demanding stattus, you need to specifically request a refresh
        # TODO health check function
        return jsonify(
            APIResponse.SystemInfoResponse(message="Health check successful", system_data={
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
        processes: list[psutil.Process] = []
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            processes.append(proc.info)
        return jsonify(APIResponse.ProcessResponse(message="List of current processes on {self.name}",
                                                   processes=processes).to_dict()), 200

    # @app.route('/api/processes/<int:process_id>', methods=['GET'])
    def get_process_status(self, process_id):
        """ Check the status of a specific process """
        try:
            process = psutil.Process(process_id)
            # TODO Cambiar el tipo de dato del segundo parametro de APIResponse a any y manejarlo en la recepcion del JSON
            return jsonify(
                APIResponse.SystemInfoResponse(process.as_dict(attrs=['pid', 'name', 'status'])).to_dict()), 200
        except psutil.NoSuchProcess:
            return jsonify(APIResponse.ErrorResponse('Process not found').to_dict()), 404

    # @app.route('/api/processes/kill', methods=['POST'])
    def kill_process(self):
        """ Kill a specific process by ID """
        data = request.json
        process_id = data.get('process_id')

        if process_id is None:
            return jsonify(APIResponse.ErrorResponse('Missing process_id').to_dict()), 400

        try:
            process = psutil.Process(process_id)
            process.terminate()
            return jsonify(APIResponse.SuccessResponse('Process {process_id} terminated').to_dict()), 200
        except psutil.NoSuchProcess:
            return jsonify(APIResponse.ErrorResponse('Process not found').to_dict()), 404
        except Exception as e:
            return jsonify(APIResponse.ErrorResponse(str(e)).to_dict()), 500

    # @app.route('/api/programs/sync', methods=['POST'])
    def sync_programs(self):
        """ Sync programs from JSON configuration """
        if not os.path.exists(CONFIG_PATH):
            return jsonify(APIResponse.ErrorResponse('Configuration file not found').to_dict()), 500

        with open(CONFIG_PATH, 'r') as f:
            try:
                programs = json.load(f)
            except json.JSONDecodeError:
                return jsonify(APIResponse.ErrorResponse('Invalid JSON format').to_dict()), 500

        return jsonify(APIResponse.ErrorResponse(programs).to_dict()), 200

    # @app.route('/api/programs', methods=['GET'])
    def get_programs(self):
        """ Get a list of all programs from JSON """
        if not os.path.exists(CONFIG_PATH):
            return jsonify(APIResponse.ErrorResponse('Configuration file not found').to_dict()), 500

        with open(CONFIG_PATH, 'r') as f:
            programs = json.load(f)

        return jsonify(APIResponse.SuccessResponse(programs).to_dict()), 200

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
        return jsonify(APIResponse.SuccessResponse(system_info).to_dict()), 200

    # @app.route('/api/system/logs', methods=['GET'])
    def get_system_logs(self):
        """ Get the latest system logs (Windows Event Logs) """
        logs = {}
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
            return jsonify(APIResponse.ErrorResponse('win32evtlog not available').to_dict()), 500
        except Exception as e:
            return jsonify(APIResponse.ErrorResponse(str(e)).to_dict()), 500

        return jsonify(APIResponse.SuccessResponse("", logs).to_dict()), 200

