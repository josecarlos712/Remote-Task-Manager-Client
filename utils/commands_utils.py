import logging
import os
from typing import Dict, Any

from flask import Flask, Response
from pip._internal.utils.deprecation import deprecated

from commands.blueprint_command.command import CommandEndpoint
from utils import APIResponse

logger = logging.getLogger(__name__)


# def load_commands_from_json():
#     """
#     Reads commands from a JSON file and synchronizes them with the database.
#     Handles creation, update, and deletion of Command objects based on the JSON content.
#     """
#     COMMANDS_JSON_PATH = configuration['COMMANDS_JSON_PATH']
#     logger.info(f"Attempting to load commands from {COMMANDS_JSON_PATH}")
#
#     # If the JSON file does not exist, create it with an example
#     if not os.path.exists(COMMANDS_JSON_PATH):
#         logger.warning(f"Commands JSON file not found at: {COMMANDS_JSON_PATH}. Creating with default content.")
#
#         # Define the default content for the JSON file
#         default_commands_data = {
#             "hello_world": {
#                 "name": "Hello World",  # Added a name for the command
#                 "description": "Sends a simple hello world message from the server.",
#                 "args": [],  # There are no arguments for this command
#                 "handler": "hello_world"  # Points to commands/hello_world.py
#             }
#         }
#         # Ensure the directory for the JSON file exists
#         COMMANDS_JSON_DIR = os.path.dirname(COMMANDS_JSON_PATH)
#         os.makedirs(COMMANDS_JSON_DIR, exist_ok=True)
#
#         try:
#             # Write the default content to the file
#             with open(COMMANDS_JSON_PATH, 'w', encoding='utf-8') as f:
#                 json.dump(default_commands_data, f, indent=2)  # Use indent for readability
#             logger.info(f"Created default commands JSON file at: {COMMANDS_JSON_PATH}")
#
#         except Exception as e:
#             logger.error(f"Error creating default commands JSON file at {COMMANDS_JSON_PATH}: {e}", exc_info=True)
#             # If file creation fails, we can't proceed.
#             return False  # Indicate failure
#         # After creating the file, proceed to load commands from it
#         # The rest of the function will now read the newly created file.
#
#     try:
#         with open(COMMANDS_JSON_PATH, 'r', encoding='utf-8') as f:
#             commands_data = json.load(f)
#         logger.info("Successfully read commands JSON file.")
#
#     except json.JSONDecodeError as e:
#         # Handle JSON decoding errors by raising a ValueError
#         logger.error(f"Error decoding JSON from {COMMANDS_JSON_PATH}. Please check the file format.", exc_info=True)
#         # Raising an exception here is appropriate as invalid JSON is a critical configuration error.
#         raise ValueError(f"Invalid JSON format in commands file: {COMMANDS_JSON_PATH}") from e
#
#     except Exception as e:
#         logger.error(f"An unexpected error occurred while reading {COMMANDS_JSON_PATH}: {e}", exc_info=True)
#         # Handle other file reading errors
#         raise IOError(f"An error occurred while reading commands file: {COMMANDS_JSON_PATH}") from e
#
#     # Get all existing command_ids from the database
#     existing_command_ids = set(Command.objects.values_list('command_id', flat=True))
#     json_command_ids = set(commands_data.keys())
#
#     # Create new or Update existing commands
#     for command_id, details in commands_data.items():
#         name = details.get('name', command_id)  # Use command_id as fallback name
#         description = details.get('description', 'No description provided.')
#         # The 'handler' and 'args' are not stored in the Command model,
#         # but are used by the execution logic.
#
#         try:
#             command, created = Command.objects.get_or_create(
#                 command_id=command_id,
#                 defaults={
#                     'name': name,
#                     'description': description
#                 }
#             )
#
#             if created:
#                 logger.info(f"Created new command: {command_id}")
#             else:
#                 # Check if existing command needs updating (Case 2)
#                 if command.name != name or command.description != description:
#                     command.name = name
#                     command.description = description
#                     command.save()
#                     logger.info(f"Updated existing command: {command_id}")
#                 # Case 1: Exists and is identical - implicitly handled by get_or_create not updating defaults
#
#         except Exception as e:
#             logger.error(f"Error processing command {command_id}: {e}", exc_info=True)
#             # The command creation or update failed, log the error. The command is skipped
#
#     # Delete commands not in JSON
#     commands_to_delete_ids = existing_command_ids - json_command_ids
#     if commands_to_delete_ids:
#         for command_id in commands_to_delete_ids:
#             logger.info(f"Command with ID '{command_id}' not found in JSON. Deleting from database.")
#             # Call the function to remove the command
#             remove_command_by_id(command_id)  # Call the function to remove the command
#     else:
#         logger.info("No commands to delete from the database.")
#
#     logger.info("Command synchronization with database completed.")
#     return True  # Indicate success

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
        logger.info(f"{__file__} - Discovering commands in directory: {commands_folder}")
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
                            logger.info(f"{__file__} - Command '{command_name}' registered successfully.")
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

        return self.command_endpoints[command](**command_kargs)

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
