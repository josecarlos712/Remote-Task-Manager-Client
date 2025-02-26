import logging
import threading
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union, Callable

from flask import jsonify
import subprocess, os

import config
from config import LogLevel
from utils import APIResponse


class ProgramExecutor:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = config.logger
        self.running_processes = {}
        self._process_counter = 0
        self._lock = threading.Lock()

    def _get_next_process_id(self) -> int:
        with self._lock:
            self._process_counter += 1
            return self._process_counter

    def execute_program(self,
                        file_path: Union[str, Path],
                        args: Optional[list] = None,
                        timeout: Optional[int] = None,
                        working_dir: Optional[Union[str, Path]] = None,
                        capture_output: bool = False,
                        on_complete: Optional[Callable] = None) -> int:
        """
        Executes an .exe or .bat file in a separate thread.

        Args:
            file_path: Path to the .exe or .bat file
            args: List of command line arguments
            timeout: Maximum execution time in seconds
            working_dir: Working directory for the program
            capture_output: Whether to capture stdout and stderr
            on_complete: Callback function to be called when execution completes
                        The callback receives the result dictionary as an argument

        Returns:
            int: Process ID that can be used to check status later
        """
        file_path = Path(file_path)
        process_id = self._get_next_process_id()

        # Initialize result dictionary
        result = {
            'process_id': process_id,
            'status': 'starting',
            'returncode': None,
            'stdout': None,
            'stderr': None,
            'error': None,
            'process': None  # Store the subprocess.Popen object here
        }

        self.running_processes[process_id] = result

        def execution_thread():
            try:
                # Validate file
                if not file_path.exists():
                    raise FileNotFoundError(f"The file '{file_path}' does not exist.")

                if file_path.suffix.lower() not in ['.exe', '.bat']:
                    raise ValueError(f"Invalid file type '{file_path.suffix}'. Must be .exe or .bat")

                if not os.access(file_path, os.X_OK):
                    raise PermissionError(f"No execute permission for '{file_path}'")

                # Prepare command
                command = [str(file_path)]
                if args:
                    command.extend(args)

                # Update status
                result['status'] = 'running'

                # Execute program
                process = subprocess.Popen(
                    args=command,
                    shell=False,
                    cwd=working_dir,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True
                )

                # Store the process object
                result['process'] = process

                # Wait for the process to complete
                stdout, stderr = process.communicate(timeout=timeout)

                # Update result
                result['status'] = 'completed'
                result['returncode'] = process.returncode
                if capture_output:
                    result['stdout'] = stdout
                    result['stderr'] = stderr

                self.logger.info(f"Process {process_id} completed with return code: {process.returncode}")

            except subprocess.TimeoutExpired:
                result['status'] = 'timeout'
                result['error'] = f"Process {process_id} timed out after {timeout} seconds"
                process.kill()  # Kill the process if it times out
                stdout, stderr = process.communicate()  # Capture any remaining output
                if capture_output:
                    result['stdout'] = stdout
                    result['stderr'] = stderr
                self.logger.error(f"Process {process_id} timed out after {timeout} seconds")

            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
                self.logger.error(f"Process {process_id} failed: {str(e)}", exc_info=True)

            finally:
                if on_complete:
                    try:
                        on_complete(result.copy())
                    except Exception as e:
                        self.logger.error(f"Callback error for process {process_id}: {str(e)}")

        # Start execution thread
        thread = threading.Thread(target=execution_thread)
        thread.daemon = True  # Thread will be terminated when main program exits
        thread.start()

        return process_id

    def get_process_status(self, process_id: int) -> dict:
        """
        Get the current status of a process.

        Args:
            process_id: The ID returned by execute_program

        Returns:
            dict: Current status and results of the process
        """
        return self.running_processes.get(process_id, {'status': 'not_found'})

    def is_running(self, process_id: int) -> bool:
        """
        Check if a process is still running.

        Args:
            process_id: The ID returned by execute_program

        Returns:
            bool: True if the process is still running
        """
        status = self.get_process_status(process_id)
        return status['status'] == 'running'

    def kill(self, process_id: int) -> bool:
        """
        Kill a running process.

        Args:
            process_id: The ID returned by execute_program

        Returns:
            bool: True if the process was successfully killed, False otherwise
        """
        status = self.get_process_status(process_id)
        if status['status'] != 'running':
            self.logger.warning(f"Process {process_id} is not running.")
            return False

        process = status.get('process')
        if process:
            try:
                process.kill()
                status['status'] = 'killed'
                self.logger.info(f"Process {process_id} has been killed.")
                return True
            except Exception as e:
                self.logger.error(f"Failed to kill process {process_id}: {str(e)}")
                return False
        else:
            self.logger.warning(f"No process object found for process {process_id}.")
            return False


class Command:
    # v2 (the version must coincide with the server side)
    def __init__(self, command, function, description="None", needs_message=False):
        """
        Constructor that initializes the Command object with a command string and a function.
        """
        self._command = command  # Store the command
        self._function = function  # Store the function reference
        self._description = description  # Store the command description
        self._needs_message = needs_message  # Obligatority of extra data for the correct function

    def execute(self, message=None):
        """
        Executes the function stored in the 'function' field with the given message as a parameter.
        """
        if self._needs_message:
            return self._function(message)  # Call the stored function with the message
        else:
            return self._function()

    def needs_message(self):
        return self._needs_message


def test_command(message=None):
    #This function is for testing
    if message:
        return jsonify(
            APIResponse.SuccessResponse(f"Command test_command executed with message {message}.").to_dict()
        ), 200
    else:
        return jsonify(
            APIResponse.SuccessResponse("Command test_command executed correctly.").to_dict()
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


class CommandsFunctions(Enum):
    TestFunction = test_command
    PopUp = show_popup
    ExecuteProgram = execute_program
