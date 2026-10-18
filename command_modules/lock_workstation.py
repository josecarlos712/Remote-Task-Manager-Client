import ctypes
import platform

from config import logger

COMMAND_ID = "lock_workstation"
TITLE = "Lock Workstation"
DESCRIPTION = "Locks the Windows desktop session."
ARGS = []


def handler(**kwargs):
    if platform.system() != "Windows":
        return "lock_workstation is only supported on Windows.", 501
    logger.info("lock_workstation invoked")
    result = ctypes.windll.user32.LockWorkStation()
    if result:
        return "Workstation lock requested.", 200
    return "Failed to lock workstation.", 500
