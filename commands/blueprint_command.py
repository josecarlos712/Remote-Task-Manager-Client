# This is a template file for creating new commands.
# 1. Copy this file to your 'api/commands/commands/' directory.
# 2. Rename it to a descriptive name (e.g., 'get_user.py', 'send_email.py').
# 3. Fill in the placeholders marked with 'YOUR_COMMAND_NAME' and add your logic.

from typing import Dict, Any, List, Optional, Tuple, Union

from flask import Flask

from commands import Command

# It's good practice to have a logger for each module
import logging

logger = logging.getLogger(__name__)


class CommandEnpoint:
    """
    This class represents a command endpoint in the API.
    It is used to define the command's metadata and handler function.
    """

    def __init__(self, title: str, description: str, args_types: Optional[List[Dict[str, Any]]] = None):
        self.command = Command.Command(
            name=__file__.split('/')[-1].replace('.py', ''),  # Use the filename as the command name. This ensures the unique identificator is not duplicated.
            title=title,
            function=self.handler,  # Point to the 'handler' function defined above
            description=description,
            args_types=args_types
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommandEnpoint):
            return NotImplemented
        return self.command == other.command

    def __getitem__(self, item):
        """
        Allows accessing command attributes using dictionary-like syntax.
        """
        if item == 'name':
            return self.command['name']
        elif item == 'title':
            return self.command['title']
        elif item == 'description':
            return self.command['description']
        elif item == 'args':
            return self.command['args_types']
        else:
            raise KeyError(f"'{item}' is not a valid command attribute.")

    # Command Handler Function
    def handler(self, args: Dict[str, Any]) -> tuple[Any, int]:
        """
        Handles the logic for the 'YOUR_COMMAND_NAME' command.

        :param args: (Dict[str, Any]): A dictionary containing consolidated arguments
                                   (URL path params, query params, JSON body).
                                   Access command-specific parameters using args.get('param_name').

        :returns: tuple[str, Any]: A tuple containing the command status and a dictionary with response data.
                             The first element is a string indicating the command status,
                             and the second element is a HTTP code for the resulting command.
        """
        logger.info(f"Executing YOUR_COMMAND_NAME command with arguments: {args}")
        # Check if required arguments are present
        required_args = self.command['args_types']
        for arg in required_args:
            if arg['required'] and arg['name'] not in args:
                error_message = f"Missing required argument: {arg['name']}"
                logger.error(error_message)
                return error_message, 400 # Return 400 Bad Request if required argument is missing

        # Execute the command logic.
        response, code = helper_function(args)

        # Return the data that will be included in the API response's 'data' field.
        return response, code


# Command Registration Function
# This function is called by the main command loader (_load_all_commands in endpoint.py).
def register() -> Tuple[CommandEnpoint | str, int]:
    """
    Registers this specific command with the global command registry.

    :param app: Flask: The Flask application instance. Passed by the _load_all_commands function.
                   Only needed if this command needs to register its own specific Flask routes
                   beyond what the general command dispatcher handles (rare for these types of commands).
    :param path: str: The base path for this command. Passed by the _load_all_commands function.
                    (Typically ignored here unless you need to build specific sub-routes).

    :returns Tuple[Union[str, Command], int]: A tuple containing the Command object and 200 on success,
                                         or an error message string and an HTTP status code on failure.
    """
    # --- Define Command Metadata ---
    # These values will be used to describe your command in the API listing.
    command_title = "Your Command Display Title"  # <--- User-friendly title (e.g., "Retrieve User Details")
    command_description = "A brief description of what this command does and its purpose."

    # Define expected arguments for documentation and potential validation.
    # This list will be included in the 'args' field of the command's metadata
    # when '/api/commands/<str:name>' is accessed.
    # Format: [{"name": "param_name", "type": "str|int|bool|list|dict", "required": True|False, "description": "..."}]
    command_args_types: List[Dict[str, Any]] = [
        # List the aguments the handler expects to receive.
        # Example for a command that takes a 'user_id' (int, required) and 'verbose' (bool, optional):
        # {
        #     "name": "user_id",
        #     "type": "int",
        #     "required": True,
        #     "description": "The unique integer ID of the user to retrieve."
        # },
        # {
        #     "name": "verbose",
        #     "type": "bool",
        #     "required": False,
        #     "description": "If true, return more detailed information about the user."
        # }
    ]

    # Create an instance of the Command class
    commandenpoint_instance = CommandEnpoint(
        title=command_title,
        description=command_description,
        args_types=command_args_types
    )

    logger.info(f"Command '{commandenpoint_instance['name']}' prepared for registration.")
    return commandenpoint_instance, 200


# This is a helper function that contains the actual logic of the command.
def helper_function(args) -> tuple[str, int]:
    return "Example function executed successfully.", 200




