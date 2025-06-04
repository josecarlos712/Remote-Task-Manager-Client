import logging
import json
import os
from typing import Dict

from flask import Flask

from commands.Command import Command
from commands.blueprint_command import CommandEnpoint

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
        self.command_endpoints = {}

    def discover_commands(self):
        """
        Discovers and loads commands from the commands folder. Then it stores it on internal state self.command_endpoints as a dictionary.
        """
        import importlib
        from commands.blueprint_command import CommandEnpoint

        # Load all the commands from the commands folder. Get all the files inside 'commands' directory and import them.
        commands_folder = os.path.join(os.path.dirname(__file__), '..', 'commands')
        logger.info(f"Discovering commands in directory: {commands_folder}")
        if not os.path.isdir(commands_folder):
            logger.error(f"Commands directory not found at expected path: {commands_folder}")
            return {}  # Not Found
        excluded_files = {'__init__.py', 'blueprint_command.py', 'Command.py'}

        # Register all the endpoints inside the folder
        commands_items = os.listdir(commands_folder)
        registered_commands = {}
        for item in commands_items:
            full_path = os.path.join(commands_folder, item)

            if item.endswith('.py') and os.path.isfile(full_path) and item not in excluded_files:
                command_name = item[:-3]  # Remove the '.py' extension
                try:
                    # Import the command module dynamically
                    logger.info(f"Importing command module: {command_name}")
                    module = importlib.import_module(f'commands.{command_name}')
                    if hasattr(module, 'register'):
                        command_endpoint, code = module.register()
                        if code == 200:
                            logger.info(f"Command '{command_name}' registered successfully.")
                            registered_commands[command_name] = command_endpoint
                        else:
                            logger.error(f"Failed to register command '{command_name}'. {command_endpoint}")
                except ImportError as e:
                    logger.error(f"Error importing command '{command_name}': {e}")

        logger.info(f"Discovered {len(registered_commands)} commands.")
        self.command_endpoints = registered_commands
        return f"Discovered {len(registered_commands)} commands.", 200

    def _register_command_endpoints(self, app: Flask, endpoint: str) -> tuple[str, int]:
        """
        Registers all command endpoints with the Flask application.
        :param app: Flask: The Flask application instance.
        :param endpoint: str: The base endpoint for the commands.

        :return: tuple[str, int]: A tuple containing a success message and HTTP status code.
        """

        if self.command_endpoints.__len__() > 0:
            logger.info("There are no commands to register.")
            return "There are no commands to register.", 200

        count = 0
        for command_name, command_endpoint in self.command_endpoints.items():
            # Assuming each command has a 'register' method to register its endpoint
            if hasattr(command_endpoint, 'register'):
                response, status_code = command_endpoint.register(app, endpoint)
                if status_code != 200:
                    logger.error(f"Failed to register command '{command_name}': {response}")
                    continue
                count += 1

        logger.info(f"Successfully registered {count} command endpoints of {self.command_endpoints.__len__()}.")
        return f"Successfully registered {count} command endpoints of {self.command_endpoints.__len__()}.", 200

    def get_command_list(self) -> Dict[str, CommandEnpoint]:
        """
        Returns the list of command endpoints.

        Returns:
            Dict[str, CommandEnpoint]: A dictionary of command endpoints.
        """
        return self.command_endpoints

    def __getitem__(self, name: str) -> tuple[CommandEnpoint | str, int]:
        """
        Retrieves a command by its name from the registered commands.
        :param name: str: The name of the command to retrieve.
        :return: tuple[Command | str, int]: A tuple containing the command object or an error message and HTTP status code.
        """
        if not name:
            logger.error("Command name is empty.")
            return "Command name cannot be empty.", 400
        if name in self:
            command_endpoint = self.command_endpoints[name]
            if isinstance(command_endpoint, CommandEnpoint):
                return command_endpoint, 200

    def __contains__(self, item) -> bool:
        """
        Checks if a command with the given name exists in the registered commands.
        :param item: str: The name of the command to check.
        :return: bool: True if the command exists, False otherwise.
        """
        return item in self.command_endpoints
