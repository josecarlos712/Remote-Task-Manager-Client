# -*- coding: utf-8 -*-
import shlex
from pathlib import Path

from commands import ProgramExecutor
from config import logger

COMMAND_ID = "execute_program"
TITLE = "Execute Program"
DESCRIPTION = "Runs a local .exe/.bat/.cmd and tracks its OS PID for later stop."
ARGS = [
    {
        "name": "path",
        "type": "str",
        "required": True,
        "description": "Absolute path to .exe or .bat",
    },
    {
        "name": "args",
        "type": "str",
        "required": False,
        "description": "Optional argument string (space-separated)",
    },
    {
        "name": "work_dir",
        "type": "str",
        "required": False,
        "description": "Optional working directory",
    },
    {
        "name": "program_key",
        "type": "str",
        "required": False,
        "description": "Optional stable key (e.g. program name) for tracking.",
    },
]


def _parse_args(extra):
    if extra is None or extra == "":
        return []
    if isinstance(extra, list):
        return [str(a) for a in extra]
    if isinstance(extra, str):
        try:
            return shlex.split(extra, posix=False)
        except ValueError:
            return extra.split()
    return [str(extra)]


def handler(**kwargs):
    path = kwargs.get("path") or kwargs.get("message")
    if not path:
        return "Missing required argument: path", 400

    file_path = Path(path)
    if not file_path.exists():
        return f"File not found: {path}", 404
    if file_path.suffix.lower() not in (".exe", ".bat", ".cmd"):
        return "Only .exe/.bat/.cmd are allowed.", 400

    work_dir = (kwargs.get("work_dir") or "").strip()
    cwd = work_dir if work_dir and Path(work_dir).exists() else str(file_path.parent)
    program_key = (kwargs.get("program_key") or file_path.name).strip()

    executor = ProgramExecutor.get()
    result = executor.execute_program(
        file_path=file_path,
        args=_parse_args(kwargs.get("args")),
        working_dir=cwd,
        program_key=program_key,
        wait=False,
    )

    if result.get("status") == "error":
        return result.get("error") or "Failed to start program", 500

    logger.info(
        f"execute_program started path={path} pid={result.get('pid')} process_id={result.get('process_id')}"
    )
    return {
        "started": True,
        "pid": result.get("pid"),
        "process_id": result.get("process_id"),
        "path": str(file_path),
        "program_key": program_key,
        "status": result.get("status"),
        "command": [str(file_path)] + _parse_args(kwargs.get("args")),
        "cwd": cwd,
    }, 200
