import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Union, Callable

import subprocess, os


logger = logging.getLogger(__name__)


class ProgramExecutor:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
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
