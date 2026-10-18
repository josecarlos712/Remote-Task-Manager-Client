import subprocess

from config import logger

COMMAND_ID = "shutdown"
TITLE = "Shutdown PC"
DESCRIPTION = "Initiates a remote shutdown after an optional delay (Windows)."
ARGS = [
    {
        "name": "time",
        "type": "int",
        "required": False,
        "description": "Delay in seconds before shutdown (default 0).",
    }
]


def handler(**kwargs):
    delay = kwargs.get("time", 0)
    try:
        delay = int(delay or 0)
    except (TypeError, ValueError):
        return "Invalid 'time' argument", 400

    # /t sets delay; /f forces running apps to close
    cmd = ["shutdown", "/s", "/f", "/t", str(max(0, delay))]
    logger.info(f"shutdown executing: {cmd}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return f"Shutdown scheduled in {delay} seconds.", 200
    except subprocess.CalledProcessError as e:
        logger.error(f"shutdown failed: {e.stderr or e}")
        return f"Shutdown failed: {e.stderr or e}", 500
    except FileNotFoundError:
        return "shutdown command not available on this OS.", 501
