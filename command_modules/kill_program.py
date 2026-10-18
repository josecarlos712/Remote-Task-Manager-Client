# -*- coding: utf-8 -*-
"""Stop a previously started program by OS PID (or tracked process_id)."""
from commands import ProgramExecutor
from config import logger

COMMAND_ID = "kill_program"
TITLE = "Kill Program"
DESCRIPTION = "Stops a running program using its OS PID (process tree on Windows)."
ARGS = [
    {
        "name": "pid",
        "type": "int",
        "required": False,
        "description": "Operating system process ID to kill.",
    },
    {
        "name": "process_id",
        "type": "int",
        "required": False,
        "description": "Internal tracker id returned by execute_program.",
    },
    {
        "name": "program_key",
        "type": "str",
        "required": False,
        "description": "Optional key used when the program was started.",
    },
]


def handler(**kwargs):
    pid = kwargs.get("pid")
    process_id = kwargs.get("process_id")
    program_key = kwargs.get("program_key")

    try:
        pid = int(pid) if pid not in (None, "") else None
    except (TypeError, ValueError):
        return "Invalid pid", 400
    try:
        process_id = int(process_id) if process_id not in (None, "") else None
    except (TypeError, ValueError):
        return "Invalid process_id", 400

    if pid is None and process_id is None and not program_key:
        return "Provide pid, process_id or program_key", 400

    executor = ProgramExecutor.get()
    if process_id is None and program_key:
        process_id = executor.find_process_id(program_key=str(program_key))

    result = executor.kill(process_id=process_id, pid=pid)
    logger.info(f"kill_program result={result}")
    if result.get("killed"):
        return result, 200
    return result.get("message") or "Could not kill process", 404
