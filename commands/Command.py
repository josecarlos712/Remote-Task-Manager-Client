import logging
import threading
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union, Callable

from flask import jsonify
import subprocess, os

import config
from utils import APIResponse
from utils.programs import ProgramExecutor


_registered_commands = {}  # Dictionary to store registered commands


class Command:
    # v2 (the version must coincide with the server side)
    def __init__(self, name, title, function, description="None", args_types=None):
        """
        Constructor that initializes the Command object with a command string and a function.
        """
        if args_types is None:
            self._args_types = []
        self._name = name  # Store the command
        self._title = title  # Store the command title
        self._function = function  # Store the function reference
        self._description = description  # Store the command description

    def execute(self, args: dict):
        """
        Executes the function stored in the 'function' field with the given message as a parameter.
        """
        return self._function(args)  # Call the stored function with the args

    def to_dict(self):
        """
        Converts the Command object to a dictionary representation.

        Returns:
            dict: A dictionary containing the command details.
        """
        return {
            'name': self._name,
            'title': self._title,
            'command': self._name,
            'description': self._description,
            'args': self._args_types,
        }

    def __getitem__(self, item):
        """
        Allows accessing command attributes using dictionary-like syntax.
        """
        if item == 'name':
            return self._name
        elif item == 'title':
            return self._title
        elif item == 'description':
            return self._description
        elif item == 'args':
            return self._args_types
        else:
            raise KeyError(f"'{item}' is not a valid command attribute.")

    __eq__ = lambda self, other: isinstance(other, Command) and self._name == other._name


def add_command(command: Command) -> tuple[str, int]:
    """
    Adds a command to the registered commands dictionary.

    Args:
        command (Command): The Command object to be added.

    Returns:
        tuple[str, int]: A tuple containing a success message and HTTP status code.
    """
    if not isinstance(command, Command):
        logging.error("Invalid command object provided.")
        return "Invalid command object provided.", 400  # Bad Request

    if command['name'] in _registered_commands:
        logging.warning(f"Command '{command['name']}' is already registered.")
        return f"Command '{command['name']}' is already registered.", 409  # Conflict

    _registered_commands[command['name']] = command
    logging.info(f"Command '{command['name']}' registered successfully.")
    return f"Command '{command['name']}' registered successfully.", 200  # OK


def get_all_commands() -> tuple[Dict[str, Command], int]:
    """
    Retrieves all registered commands.

    Returns:
        tuple[Dict[str, Command], int]: A tuple containing a dictionary of all registered commands and HTTP status code.
    """
    if not _registered_commands:
        logging.warning("No commands registered.")
        return {}, 404  # Not Found

    logging.info("Retrieved all registered commands.")
    return _registered_commands, 200  # OK


def get_command(name: str = "None") -> tuple[str|Command, int]:
    """
    Retrieves a command by its name from the registered commands.

    Args:
        name (str): The name of the command to retrieve.

    Returns:
        Command: The Command object if found, otherwise None.
    """
    # Check if parameter is a valid string
    if not isinstance(name, str) or not name:
        logging.error("Invalid command name provided.")
        return "Invalid command name provided.", 400  # Bad Request
    if name == "None":
        logging.warning(f"Command name must be a valid existing command name. Got '{name}'")
        return f"Command name must be a valid existing command name. Got '{name}'", 400  # Bad Request

    # Retrieve the command from the registered commands dictionary
    if name not in _registered_commands:
        logging.error(f"Command '{name}' not found.")
        return f"Command '{name}' not found.", 404  # Not Found

    return _registered_commands.get(name)


def execute_program():
    def on_program_complete(result):
        print(f"Program completed! Result: {result}")

    # Create executor instance
    executor = ProgramExecutor()

    # Execute a program
    process_id = executor.execute_program(
        file_path="path/to/your/program.exe",
        args=["--verbose"],
        timeout=30,
        capture_output=True,
        on_complete=on_program_complete
    )

    # Main program can continue running while the program executes
    print(f"Started process with ID: {process_id}")

    # You can check status at any time
    status = executor.get_process_status(process_id)
    print(f"Current status: {status['status']}")

    # Check if still running
    is_running = executor.is_running(process_id)
    print(f"Is running: {is_running}")