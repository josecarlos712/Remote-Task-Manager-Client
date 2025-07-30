# This is a template file for creating new commands.
# 1. Copy this file to your 'api/commands/commands/' directory.
# 2. Rename it to a descriptive name (e.g., 'get_user.py', 'send_email.py').
# 3. Fill in the placeholders marked with 'YOUR_COMMAND_NAME' and add your logic.


# Basic imports
from typing import Dict, Any, List, Optional, Tuple
from flask import Response
from commands.Command import Command
import logging
from utils import APIResponse
import os
# Specific command imports


logger = logging.getLogger(__name__)


class CommandEndpoint:
    """
    This class represents a command endpoint in the API.
    It is used to define the command's metadata and handler function.
    """

    def __init__(self, title: str, description: str, args_types: Optional[List[Dict[str, Any]]] = None):
        if args_types is None:
            args_types = []

        command_directory = os.path.dirname(__file__)
        command_name = os.path.basename(command_directory)

        self.command = Command(
            name=command_name,
            # Use the filename as the command name. This ensures the unique identificator is not duplicated.
            title=title,
            function=self,  # Point to the 'handler' function
            description=description,
            args_types=args_types
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommandEndpoint):
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
    def __call__(self, **kwargs: Dict[str, Any]) -> Response:
        """
        Handles the logic for the 'YOUR_COMMAND_NAME' command.

        :param args: (Dict[str, Any]): A dictionary containing consolidated arguments
                                   (URL path params, query params, JSON body).
                                   Access command-specific parameters using args.get('param_name').

        :returns: tuple[str, Any]: A tuple containing the command status and a dictionary with response data.
                             The first element is a string indicating the command status,
                             and the second element is a HTTP code for the resulting command.
        """
        logger.info(f"{__file__} - Executing YOUR_COMMAND_NAME command with arguments: {kwargs}")
        # Check if required arguments are present
        required_args = self.command['args_types']
        for arg in required_args:
            if arg['required'] and arg['name'] not in kwargs:
                error_message = f"{__file__} - Missing required argument: {arg['name']}"
                logger.error(error_message)
                return APIResponse.BadRequestResponse(
                    error_message).to_response()  # Return 400 Bad Request if required argument is missing

        # Execute the command logic.
        response, code = helper_function(**kwargs)

        # Return the data that will be included in the API response's 'data' field.
        if code == 200:
            return APIResponse.SuccessResponse(
                message=f"{self.command['name']} - Command executed successfully.",
                data=response  # Pass any status from helper
            ).to_response()
        else:
            return APIResponse.ErrorResponse(
                message=f"{self.command['name']} - Failed to execute the command: {response}",
                code=code
            ).to_response()

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the CommandEndpoint instance's command metadata to a dictionary
        for API response. Delegates to the internal Command object's to_dict method.

        Returns:
            Dict[str, Any]: A dictionary containing the command's name, title,
                            description, and arguments.
        """
        # The internal Command object already has a to_dict method
        # that returns the desired structure.
        return self.command.to_dict()


# Command Registration Function
# This function is called by the main command loader (_load_all_commands in endpoint.py).
def register() -> Tuple[CommandEndpoint | str, int]:
    """
    Registers this specific command with the global command registry.

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
    specs_command = CommandEndpoint(
        title="Generate System Specs",
        description="Collects and stores current system specs in a text file.",
        args_types=[{"output_path": "str", "type": "str", "required": False, "description": "Path to save the system specs file."}]
    )

    return specs_command, 200


def helper_function(**kwargs: Dict[str, Any]) -> Tuple[str | dict, int]:
    """
        Main handler function for API endpoint.

        Parameters:
            **kwargs (Dict[str, Any]): Request arguments and data

        Returns:
            Response: Flask response object

        Implementation Notes:
        - This function should be implemented to handle actual business logic
        - Must return a response using the APIResponse module and the method to_response()
        - Example return: APIResponse.SuccessResponse("message", data).to_response()
        - For errors: APIResponse.ErrorResponse("error message", code).to_response()
        """
    ...
    import platform
    import psutil
    import datetime

    def generate_system_specs(args: dict) -> dict:
        output_path = args.get("output_path", "system_specs.txt")

        specs = {
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "System": platform.system(),
            "Node Name": platform.node(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Machine": platform.machine(),
            "Processor": platform.processor(),
            "CPU Cores": psutil.cpu_count(logical=False),
            "Logical CPUs": psutil.cpu_count(logical=True),
            "Total RAM (GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2)
        }

        with open(output_path, "w") as f:
            for key, value in specs.items():
                f.write(f"{key}: {value}\n")

        return specs
    # Use APIResponse module for returning responses or errors.
    return generate_system_specs({}), 200
