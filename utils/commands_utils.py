import logging
import os
from typing import Dict, Any

from flask import Flask, Response
from pip._internal.utils.deprecation import deprecated

from commands.blueprint_command.command import CommandEndpoint
from utils import APIResponse

logger = logging.getLogger(__name__)


class CommandsLoader:
    """
    CommandsLoader class to handle loading and registering commands from the commands folder.
    This class is responsible for discovering, registering, and managing command endpoints.
    """

    def __init__(self, app: Flask):
        self.command_endpoints: Dict[str, CommandEndpoint] = {}

    def discover_commands(self) -> tuple[str, int]:
        """
        Discovers and loads commands from subdirectories within the 'commands' folder.
        Each command is expected to be in its own directory, with a 'command.py' file inside.
        The name of the command is the name of the folder containing 'command.py'.
        It stores discovered commands in self.command_endpoints as a dictionary.
        """
        import importlib

        commands_base_folder = os.path.join(os.path.dirname(__file__), '..', 'commands')
        logger.info(f"{__file__} - Discovering commands in base directory: {commands_base_folder}")

        if not os.path.isdir(commands_base_folder):
            logger.error(f"{__file__} - Commands base directory not found at expected path: {commands_base_folder}")
            # Consider raising an error or returning a specific error status if this is critical
            self.command_endpoints = {}
            return f"{__file__} - Commands base directory not found.", 404

        registered_commands = {}
        # Iterate through items directly inside the commands_base_folder
        for command_dir_name in os.listdir(commands_base_folder):
            command_full_path = os.path.join(commands_base_folder, command_dir_name)
            command_entry_file = os.path.join(command_full_path, 'command.py')

            # Exclude directories that are not commands
            excluded_dirs = {'__pycache__', 'blueprint_command', 'disabled'}
            # Check if it's a directory and contains the 'command.py' entry file
            if os.path.isdir(command_full_path) and os.path.isfile(
                    command_entry_file) and command_dir_name not in excluded_dirs:
                command_name = command_dir_name  # The folder name where the command.py file is located.
                try:
                    # Construct the module import path.
                    # Example: if commands_base_folder is 'your_app/commands'
                    # and command_dir_name is 'my_command',
                    # the import path becomes 'api.commands.my_command.command'
                    # The name of the command is derived from the directory name, so it would be 'my_command'.
                    module_path = f'commands.{command_name}.command'

                    logger.debug(f"{__file__} - Attempting to import command module: {module_path}")
                    module = importlib.import_module(module_path)

                    if hasattr(module, 'register'):
                        # Call the register function defined in command.py
                        command_endpoint, code = module.register()
                        if code == 200:
                            # Use the name from the command_endpoint itself for consistency
                            # (which should match command_name if setup correctly)
                            logger.info(f"{__file__} - Command '{command_name}' registered successfully.")
                            registered_commands[command_name] = command_endpoint
                        else:
                            logger.error(
                                f"{__file__} - Failed to register command '{command_name}'. Reason: {command_endpoint}")
                    else:
                        logger.warning(
                            f"{__file__} - Skipped '{command_name}': Entry file 'command.py' was found but no 'register' function.")

                except ImportError as e:
                    logger.error(f"{__file__} - Error importing command from '{command_full_path}/command.py': {e}")
                except Exception as e:
                    logger.error(
                        f"{__file__} - An unexpected error occurred during registration of '{command_full_path}': {e}",
                        exc_info=True)

        self.command_endpoints = registered_commands
        logger.info(f"{__file__} - Discovered {len(registered_commands)} commands: {list(registered_commands.keys())}")
        return f"{__file__} - Discovered {len(registered_commands)} commands.", 200

    def discover_commands_files(self):
        """
        Discovers and loads commands from the commands folder. Then it stores it on internal state self.command_endpoints as a dictionary.
        """
        import importlib
        from warnings import warn
        warn("discover_commands_files is deprecated. Use discover_commands instead.", DeprecationWarning)

        # Load all the commands from the commands folder. Get all the files inside 'commands' directory and import them.
        commands_folder = os.path.join(os.path.dirname(__file__), '..', 'commands')
        logger.debug(f"{__file__} - Discovering commands in directory: {commands_folder}")
        if not os.path.isdir(commands_folder):
            logger.error(f"{__file__} - Commands directory not found at expected path: {commands_folder}")
            return {}  # Not Found
        excluded_files = {'__init__.py', 'blueprint_command.py', 'Command.py', 'legacy_to_command.py'}

        # Register all the endpoints inside the folder
        commands_items = os.listdir(commands_folder)
        registered_commands = {}
        for item in commands_items:
            full_path = os.path.join(commands_folder, item)

            if item.endswith('.py') and os.path.isfile(full_path) and item not in excluded_files:
                command_name = item[:-3]  # Remove the '.py' extension
                try:
                    # Import the command module dynamically
                    logger.info(f"{__file__} - Importing command module: {command_name}")
                    module = importlib.import_module(f'commands.{command_name}')
                    if hasattr(module, 'register'):
                        command_endpoint, code = module.register()
                        if code == 200:
                            logger.debug(f"{__file__} - Command '{command_name}' registered successfully.")
                            registered_commands[command_name] = command_endpoint
                        else:
                            logger.error(
                                f"{__file__} - Failed to register command '{command_name}'. {command_endpoint}")
                except ImportError as e:
                    logger.error(f"{__file__} - Error importing command '{command_name}': {e}")

        logger.info(f"{__file__} - Discovered {len(registered_commands)} commands.")
        self.command_endpoints = registered_commands
        return f"{__file__} - Discovered {len(registered_commands)} commands.", 200

    def get_command_list(self) -> Dict[str, CommandEndpoint]:
        """
        Returns the list of command endpoints.

        Returns:
            Dict[str, CommandEndpoint]: A dictionary of command endpoints.
        """
        return self.command_endpoints

    def __call__(self, command, **kwargs) -> Response:
        """
        Allows the CommandsLoader instance to be called as a function.
        This can be used to trigger the discovery of commands.
        """
        if not command:
            logger.error("Command name is empty.")
            return APIResponse.ErrorResponse("Command name cannot be empty.", 400).to_response()

        # Pop the 'command' key from kwargs to avoid passing it as a parameter.
        command_kargs = kwargs.copy()
        command_kargs.pop('command', None)  # Remove 'command' from kargs to pass only parameters.

        if command not in self.command_endpoints:
            logger.error(f"Command '{command}' not found in registered commands.")
            return APIResponse.ErrorResponse(f"Command '{command}' not found.", 404).to_response()
        command_endpoint = self.command_endpoints[command]

        return command_endpoint(**command_kargs)

    def __getitem__(self, name: str) -> tuple[CommandEndpoint | Dict[str, CommandEndpoint] | str, int]:
        """
        Retrieves a command by its name from the registered commands.
        :param name: str: The name of the command to retrieve.
        :return: tuple[Command | str, int]: A tuple containing the command object or an error message and HTTP status code.
        """
        if not name:
            # Return all commands if the name is an empty string.
            logger.info("Returning all registered commands.")
            return self.command_endpoints, 200
        if name in self:
            command_endpoint = self.command_endpoints[name]
            if isinstance(command_endpoint, CommandEndpoint):
                return command_endpoint, 200

    def __contains__(self, item) -> bool:
        """
        Checks if a command with the given name exists in the registered commands.
        :param item: str: The name of the command to check.
        :return: bool: True if the command exists, False otherwise.
        """
        return item in self.command_endpoints
