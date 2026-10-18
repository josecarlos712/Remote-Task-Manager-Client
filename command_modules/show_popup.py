import threading

from config import logger

COMMAND_ID = "show_popup"
TITLE = "Show Message Window"
DESCRIPTION = "Displays a non-blocking popup message on the client desktop."
ARGS = [
    {
        "name": "message",
        "type": "str",
        "required": True,
        "description": "Text to display.",
    },
    {
        "name": "title",
        "type": "str",
        "required": False,
        "description": "Window title.",
    },
]
NEEDS_MESSAGE = True


def _show(title: str, message: str) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(title, message)
    root.destroy()


def handler(**kwargs):
    message = kwargs.get("message")
    title = kwargs.get("title") or "Notification"
    if not message:
        return "Missing required argument: message", 400

    thread = threading.Thread(target=_show, args=(title, str(message)), daemon=True)
    thread.start()
    logger.info(f"show_popup queued title={title!r} message={message!r}")
    return "Message queued for display.", 200
