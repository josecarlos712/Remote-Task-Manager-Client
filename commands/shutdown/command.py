# This is a template file for creating new commands.
# 1. Copy this file to your 'api/commands/commands/' directory.
# 2. Rename it to a descriptive name (e.g., 'get_user.py', 'send_email.py').
# 3. Fill in the placeholders marked with 'YOUR_COMMAND_NAME' and add your logic.


# Basic imports
from typing import Dict, Any, List, Optional, Tuple
from flask import Response
from commands.Command import Command
import logging
import os
from utils import APIResponse
# Specific command imports
import subprocess  # Needed for running external commands
import sys  # Needed to check OS type

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
    Registers the 'shutdown_pc' command with the global command registry.
    """
    command_title = "Shutdown PC"
    command_description = "Initiates a remote shutdown of the PC after a specified delay. This command requires appropriate system permissions."

    command_args_types: List[Dict[str, Any]] = [
        {
            "name": "time",
            "type": "int",
            "required": False,
            "description": "The delay in seconds before the PC shuts down. (e.g., no 'time' arg for immediate, 60 for 1 minute)."
        }
    ]

    command_endpoint_instance = CommandEndpoint(
        title=command_title,
        description=command_description,
        args_types=command_args_types
    )

    return command_endpoint_instance, 200


def helper_function(**kwargs: Dict[str, Any]) -> Tuple[str, int]:
    """
    Executes the system shutdown command based on the provided time.
    :param kwargs: Dict[str, Any]: Contains 'time' (int) for the shutdown delay.
    :return: Tuple[str, int]: A status message and HTTP status code.
    """
    if not 'time' in kwargs:
        # If 'time' is not provided, default to immediate shutdown
        logger.debug("No 'time' argument provided. Defaulting to immediate shutdown.")
        shutdown_time_seconds = 0
    else:
        # Extract the 'time' argument from kwargs
        logger.debug(f"Received shutdown time argument: {kwargs['time']}")
        shutdown_time_seconds = kwargs.get("time")

    if not isinstance(shutdown_time_seconds, int) or shutdown_time_seconds < 0:
        # If 'time' is not provided or is invalid, default to immediate shutdown
        shutdown_time_seconds = 0

    command_to_execute: List[str] = []

    # shutdown /s /f /t XXXX
    # /s: shutdown
    # /f: force running applications to close
    # /t XXXX: timeout in seconds
    command_to_execute = ["shutdown", "/s", "/f", "/t", str(shutdown_time_seconds)]

    logger.info(f"Attempting to execute shutdown command: {' '.join(command_to_execute)}")

    try:
        # Popen is used here instead of run to avoid blocking if stdin/stdout are not handled
        # and to specifically suppress any console window on Windows.
        # For 'shutdown', it's fire-and-forget, so Popen is suitable.
        # We use check=True with run() for direct error checking.
        result = subprocess.run(
            command_to_execute,
            check=True,  # Raise CalledProcessError if return code is non-zero
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW if sys.platform.startswith(
                'win') else 0,  # Detach & no window on Windows
            text=True  # Decode stdout/stderr as text
        )

        logger.debug(f"Shutdown command executed. Stdout: {result.stdout.strip()}, Stderr: {result.stderr.strip()}")
        return f"PC shutdown command issued successfully. System will shut down in {shutdown_time_seconds} seconds.", 200

    except FileNotFoundError:
        error_msg = f"Shutdown command not found. Ensure it's in your PATH or you have permissions."
        logger.error(error_msg, exc_info=True)
        return error_msg, 500
    except subprocess.CalledProcessError as e:
        error_msg = f"Shutdown command failed with exit code {e.returncode}. Stderr: {e.stderr.strip()}"
        logger.error(error_msg, exc_info=True)
        return error_msg, 500
    except Exception as e:
        error_msg = f"An unexpected error occurred while trying to shut down the PC: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg, 500
