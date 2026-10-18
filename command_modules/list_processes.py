from config import logger

COMMAND_ID = "list_processes"
TITLE = "List Processes"
DESCRIPTION = "Returns a snapshot of running processes (pid, name, status)."
ARGS = []


def handler(**kwargs):
    try:
        import psutil
    except ImportError:
        return "psutil is required (pip install psutil).", 501

    processes = []
    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    logger.info(f"list_processes returned {len(processes)} entries")
    return {"processes": processes, "count": len(processes)}, 200
