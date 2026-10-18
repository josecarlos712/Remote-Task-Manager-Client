# -*- coding: utf-8 -*-
"""Process/program execution helpers used by command modules."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from flask import jsonify

import config
from utils import APIResponse

logger = config.logger


class ProgramExecutor:
    """
    Tracks launched programs by an internal process_id and OS PID.
    Does not block waiting for the child to exit (unless timeout is set).
    """

    _instance: Optional["ProgramExecutor"] = None

    def __init__(self):
        self.running_processes: Dict[int, dict] = {}
        self._by_os_pid: Dict[int, int] = {}
        self._by_key: Dict[str, int] = {}
        self._process_counter = 0
        self._lock = threading.Lock()

    @classmethod
    def get(cls) -> "ProgramExecutor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_next_process_id(self) -> int:
        with self._lock:
            self._process_counter += 1
            return self._process_counter

    def execute_program(
        self,
        file_path: Union[str, Path],
        args: Optional[list] = None,
        timeout: Optional[int] = None,
        working_dir: Optional[Union[str, Path]] = None,
        capture_output: bool = False,
        on_complete: Optional[Callable] = None,
        program_key: Optional[str] = None,
        wait: bool = False,
    ) -> dict:
        """
        Start an .exe/.bat/.cmd. Returns a status dict including process_id and pid.

        On Windows, .bat/.cmd run via ``cmd /c call`` in a new console window
        so scripts like oobabooga's start_windows.bat behave like a double-click.

        By default does NOT wait for the process to finish (non-blocking).
        """
        file_path = Path(file_path)
        process_id = self._get_next_process_id()
        result: dict[str, Any] = {
            "process_id": process_id,
            "pid": None,
            "status": "starting",
            "returncode": None,
            "stdout": None,
            "stderr": None,
            "error": None,
            "process": None,
            "path": str(file_path),
            "program_key": program_key or str(file_path),
        }

        with self._lock:
            self.running_processes[process_id] = result

        try:
            if not file_path.exists():
                raise FileNotFoundError(f"The file '{file_path}' does not exist.")
            if file_path.suffix.lower() not in (".exe", ".bat", ".cmd"):
                raise ValueError(f"Invalid file type '{file_path.suffix}'. Must be .exe/.bat/.cmd")

            command: List[str] = [str(file_path)]
            if args:
                command.extend(str(a) for a in args)

            cwd = str(working_dir) if working_dir else str(file_path.parent)
            is_batch = file_path.suffix.lower() in (".bat", ".cmd")
            popen_kwargs: dict[str, Any] = {
                "cwd": cwd,
                "stdout": subprocess.PIPE if capture_output else None,
                "stderr": subprocess.PIPE if capture_output else None,
                "text": True,
            }

            if is_batch and sys.platform == "win32":
                # .bat/.cmd need cmd.exe and usually a real console window
                # (conda activate, pause, relative paths). shell=True alone
                # inherits the agent's hidden console and often exits early.
                command = ["cmd.exe", "/c", "call", str(file_path)]
                if args:
                    command.extend(str(a) for a in args)
                popen_kwargs["shell"] = False
                if not capture_output:
                    popen_kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
                process = subprocess.Popen(command, **popen_kwargs)
            else:
                popen_kwargs["shell"] = False
                process = subprocess.Popen(command, **popen_kwargs)

            result["process"] = process
            result["pid"] = process.pid
            result["status"] = "running"

            with self._lock:
                self._by_os_pid[process.pid] = process_id
                key = result["program_key"]
                if key:
                    self._by_key[str(key)] = process_id

            logger.info(
                f"ProgramExecutor started process_id={process_id} pid={process.pid} cmd={command}"
            )

            if wait or timeout is not None:
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    result["status"] = "completed"
                    result["returncode"] = process.returncode
                    if capture_output:
                        result["stdout"] = stdout
                        result["stderr"] = stderr
                except subprocess.TimeoutExpired:
                    self.kill(process_id)
                    result["status"] = "timeout"
                    result["error"] = f"Process timed out after {timeout} seconds"
            else:
                # Poll completion in background so status stays accurate
                def _watch():
                    try:
                        process.wait()
                        with self._lock:
                            if result.get("status") == "running":
                                result["status"] = "completed"
                                result["returncode"] = process.returncode
                        if on_complete:
                            on_complete(dict(result))
                    except Exception as e:
                        logger.error(f"Watcher error for process_id={process_id}: {e}")

                threading.Thread(target=_watch, daemon=True, name=f"watch-{process_id}").start()

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"ProgramExecutor failed process_id={process_id}: {e}", exc_info=True)

        return result

    def get_process_status(self, process_id: int) -> dict:
        status = self.running_processes.get(process_id)
        if not status:
            return {"status": "not_found", "process_id": process_id}
        # Refresh from OS
        proc = status.get("process")
        if proc is not None and status.get("status") == "running":
            code = proc.poll()
            if code is not None:
                status["status"] = "completed"
                status["returncode"] = code
        return {
            "process_id": status.get("process_id"),
            "pid": status.get("pid"),
            "status": status.get("status"),
            "path": status.get("path"),
            "program_key": status.get("program_key"),
            "returncode": status.get("returncode"),
            "error": status.get("error"),
        }

    def is_running(self, process_id: int) -> bool:
        status = self.get_process_status(process_id)
        return status.get("status") == "running"

    def find_process_id(self, *, pid: Optional[int] = None, program_key: Optional[str] = None) -> Optional[int]:
        with self._lock:
            if pid is not None and int(pid) in self._by_os_pid:
                return self._by_os_pid[int(pid)]
            if program_key and str(program_key) in self._by_key:
                return self._by_key[str(program_key)]
        return None

    def kill(self, process_id: Optional[int] = None, pid: Optional[int] = None) -> dict:
        """
        Kill by internal process_id and/or OS pid.
        Uses taskkill /T on Windows to stop the process tree.
        """
        if process_id is None and pid is not None:
            process_id = self.find_process_id(pid=int(pid))

        status = self.running_processes.get(process_id) if process_id is not None else None
        os_pid = None
        if status:
            os_pid = status.get("pid")
            proc = status.get("process")
            if proc is not None and os_pid is None:
                os_pid = proc.pid
        if os_pid is None and pid is not None:
            os_pid = int(pid)

        if os_pid is None:
            return {"killed": False, "message": "No PID available to kill."}

        try:
            if sys.platform == "win32":
                completed = subprocess.run(
                    ["taskkill", "/PID", str(os_pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                )
                ok = completed.returncode == 0 or "not found" in (completed.stderr or "").lower()
                message = (completed.stdout or completed.stderr or "").strip()
            else:
                os.kill(os_pid, 15)
                ok = True
                message = f"Sent SIGTERM to {os_pid}"

            if status is not None:
                status["status"] = "killed" if ok else status.get("status")
            logger.info(f"ProgramExecutor kill pid={os_pid} process_id={process_id} ok={ok} {message}")
            return {
                "killed": bool(ok),
                "pid": os_pid,
                "process_id": process_id,
                "message": message or ("killed" if ok else "kill failed"),
            }
        except Exception as e:
            logger.error(f"Failed to kill pid={os_pid}: {e}", exc_info=True)
            return {"killed": False, "pid": os_pid, "process_id": process_id, "message": str(e)}

    def list_running(self) -> list[dict]:
        out = []
        for process_id in list(self.running_processes.keys()):
            st = self.get_process_status(process_id)
            if st.get("status") == "running":
                out.append(st)
        return out


class Command:
    def __init__(self, command, function, description="None", needs_message=False):
        self._command = command
        self._function = function
        self._description = description
        self._needs_message = needs_message

    def execute(self, message=None):
        if self._needs_message:
            return self._function(message)
        return self._function()

    def needs_message(self):
        return self._needs_message


def test_command(message=None):
    if message:
        return jsonify(
            APIResponse.SuccessResponse(f"Command test_command executed with message {message}.").to_dict()
        ), 200
    return jsonify(APIResponse.SuccessResponse("Command test_command executed correctly.").to_dict()), 200


def show_popup(message=None):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Informacion", message)
    root.destroy()
    return jsonify(APIResponse.SuccessResponse("Command popup executed correctly.").to_dict()), 200


class CommandsFunctions(Enum):
    TestFunction = test_command
    PopUp = show_popup
