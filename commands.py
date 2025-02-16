from typing import Dict

from flask import jsonify
import subprocess, os

from utils import APIResponse


class Command:
    # v2 (the version must coincide with the server side)
    def __init__(self, command, function, description="None"):
        """
        Constructor that initializes the Command object with a command string and a function.
        """
        self.command = command  # Store the command
        self.function = function  # Store the function reference
        self.description = description  # Store the command description

    def execute(self, message=None):
        """
        Executes the function stored in the 'function' field with the given message as a parameter.
        """
        if message is not None:
            return self.function(message)  # Call the stored function with the message
        else:
            return self.function()


def test_command(message=None):
    #This function is for testing
    if message:
        return jsonify(
            APIResponse("success", f"Command test_command executed with message {message}.").to_dict()
        ), 200
    else:
        return jsonify(
            APIResponse("success", "Command test_command executed correctly.").to_dict()
        ), 200


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

    # Create a root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Show a popup message
    _message = message or "None"
    messagebox.showinfo("Popup", _message)

    # Close the application after the popup is closed
    root.destroy()
    return jsonify(
        APIResponse("success", "Command popup executed correctly.").to_dict()
    ), 200


def execute_program(file_path):
    """
    Executes an .exe or .bat file based on its file extension.

    Args:
        file_path (str): The full path to the .exe or .bat file.

    Returns:
        int: The exit code of the process.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Ensure the file is executable
    if not (file_path.endswith('.exe') or file_path.endswith('.bat')):
        raise ValueError("The file must be a .exe or .bat file.")

    try:
        # Execute the file
        result = subprocess.run(file_path, shell=True, check=True)
        return result.returncode  # Return the exit code of the process
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing '{file_path}': {e}")
        return e.returncode
