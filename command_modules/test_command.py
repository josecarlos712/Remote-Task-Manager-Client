from config import logger

COMMAND_ID = "test_command"
TITLE = "Test Command"
DESCRIPTION = "Simple ping-style command for smoke tests."
ARGS = [
    {
        "name": "message",
        "type": "str",
        "required": False,
        "description": "Optional message echoed back.",
    }
]
NEEDS_MESSAGE = False


def handler(**kwargs):
    message = kwargs.get("message")
    logger.info(f"test_command executed message={message!r}")
    if message:
        return f"Command test_command executed with message {message}.", 200
    return "Command test_command executed correctly.", 200
