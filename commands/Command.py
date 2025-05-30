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

    def __getitem__(self, name: str):

        if not isinstance(name, str):
            raise TypeError("'name' must be a string")
        item = name.strip().lower() # All names are lowercase



        return getattr(self, f"_{item}", None)


def show_popup(message=None):
    """
    Displays a popup message using a Tkinter messagebox.

    Args:
        message (str, optional): The message to display in the popup. Defaults to "None".

    Returns:
        tuple: A JSON response and HTTP status code indicating success.
    """
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    messagebox.showinfo("Información", message)

    # Close the application after the popup is closed
    root.destroy()
    return jsonify(
        APIResponse.SuccessResponse("Command popup executed correctly.").to_dict()
    ), 200


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