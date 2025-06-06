# File: api/commands/commands/show_message_window.py
import os
# This file defines a command to display an asynchronous message window on the client.

from typing import Dict, Any, List, Optional, Tuple, Union

from flask import Response

from commands.Command import Command

import logging

from utils import APIResponse

import threading
import queue
import tkinter as tk
from tkinter import font as tk_font
import datetime

logger = logging.getLogger(__name__)

# --- Global setup for Tkinter Thread Communication ---
_MESSAGE_QUEUE: queue.Queue = queue.Queue()
_TK_ROOT: Optional[tk.Tk] = None  # Will hold the main Tkinter root window
_TK_THREAD: Optional[threading.Thread] = None


def _run_tkinter_app():
    """
    Function to run the Tkinter main loop in a separate thread.
    This thread will create and manage all Tkinter GUI elements.
    """
    global _TK_ROOT
    _TK_ROOT = tk.Tk()
    _TK_ROOT.withdraw()  # Hide the main root window, we only need Toplevels

    # Set up periodic check for new messages in the queue
    _TK_ROOT.after(100, _check_queue_and_display_message)  # Check every 100ms
    _TK_ROOT.mainloop()
    logger.info("Tkinter main loop has stopped.")


def _check_queue_and_display_message():
    """
    Checks the message queue for new messages and displays them in a popup.
    This function runs on the Tkinter thread.
    """
    try:
        # Get message data without blocking if queue is empty
        message_data = _MESSAGE_QUEUE.get_nowait()

        message_text = message_data.get("message_text", "No message provided.")
        popup_title = message_data.get("popup_title", "Notification")
        popup_type = message_data.get("popup_type", "info")  # e.g., 'info', 'warning', 'error'
        timeout_ms = message_data.get("timeout_ms", 5000)  # Default 5 seconds

        logger.info(f"Tkinter thread received message: Title='{popup_title}', Message='{message_text}'")

        # Create a new Toplevel window for the popup
        popup = tk.Toplevel(_TK_ROOT)
        popup.title(popup_title)
        popup.attributes("-topmost", True)  # Keep popup on top of other windows

        # Basic styling based on type
        bg_color = "lightgray"
        text_color = "black"
        if popup_type == "warning":
            bg_color = "#FFD700"  # Gold
            text_color = "black"
        elif popup_type == "error":
            bg_color = "#FF6347"  # Tomato
            text_color = "white"
        elif popup_type == "success":
            bg_color = "#90EE90"  # LightGreen
            text_color = "black"

        popup.configure(bg=bg_color)

        # Use a bold font for the title in the message box, if desired
        title_font = tk_font.Font(family="Helvetica", size=12, weight="bold")
        message_font = tk_font.Font(family="Helvetica", size=10)

        # Frame to hold content, for padding and background
        content_frame = tk.Frame(popup, bg=bg_color, padx=10, pady=10)
        content_frame.pack(padx=5, pady=5)

        title_label = tk.Label(content_frame, text=popup_title, font=title_font, bg=bg_color, fg=text_color)
        title_label.pack(pady=(0, 5))

        message_label = tk.Label(content_frame, text=message_text, wraplength=300, justify="center", font=message_font,
                                 bg=bg_color, fg=text_color)
        message_label.pack(pady=(5, 10))

        # Close button
        close_button = tk.Button(content_frame, text="Close", command=popup.destroy, bg="white", fg="black")
        close_button.pack(pady=(0, 5))

        # Center the popup on the screen (basic centering)
        popup.update_idletasks()  # Ensure geometry is calculated
        x = popup.winfo_screenwidth() // 2 - popup.winfo_width() // 2
        y = popup.winfo_screenheight() // 2 - popup.winfo_height() // 2
        popup.geometry(f"+{x}+{y}")

        # Optional: Auto-destroy the popup after a timeout
        if timeout_ms > 0:
            popup.after(timeout_ms, popup.destroy)

    except queue.Empty:
        # No message in queue, do nothing
        pass
    except Exception as e:
        logger.error(f"Error in Tkinter message display: {e}", exc_info=True)
    finally:
        # Schedule the next check
        if _TK_ROOT and _TK_ROOT.winfo_exists():  # Check if root still exists
            _TK_ROOT.after(100, _check_queue_and_display_message)


def _start_tkinter_thread():
    """
    Starts the Tkinter application in a separate daemon thread.
    This should be called only once when your Flask app starts.
    """
    global _TK_THREAD
    if _TK_THREAD is None or not _TK_THREAD.is_alive():
        _TK_THREAD = threading.Thread(target=_run_tkinter_app, daemon=True)
        _TK_THREAD.start()
        logger.debug("Tkinter GUI thread started.")
    else:
        logger.debug("Tkinter GUI thread is already running.")


_start_tkinter_thread()


class CommandEndpoint:
    """
    This class represents a command endpoint in the API for showing messages.
    It is used to define the command's metadata and handler function.
    """

    def __init__(self, title: str, description: str, args_types: Optional[List[Dict[str, Any]]] = None):
        if args_types is None:
            args_types = []

        command_directory = os.path.dirname(__file__)
        command_name = os.path.basename(command_directory)

        self.command = Command(
            name=command_name,
            # Use the filename as the command name. This ensures the unique identificator is not duplicated.
            title=title,
            function=self,  # Point to the instance's __call__ method as the handler
            description=description,
            args_types=args_types
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, CommandEndpoint):
            return NotImplemented
        return self.command == other.command

    def __getitem__(self, item: str) -> Any:
        """
        Allows accessing command attributes using dictionary-like syntax.
        """
        if item == 'name':
            return self.command['name']
        elif item == 'title':
            return self.command['title']
        elif item == 'description':
            return self.command['description']
        elif item == 'args':
            return self.command['args_types']
        else:
            raise KeyError(f"'{item}' is not a valid command attribute for CommandEndpoint.")

    def get_command_object(self) -> Command:
        """Helper to explicitly get the internal Command object."""
        return self.command

    # Command Handler Function (this is the __call__ method)
    def __call__(self, **kwargs: Dict[str, Any]) -> Response:
        """
        Handles the logic for the 'show_message_window' command.
        This command sends a message to be displayed on an asynchronous client window.

        Args:
            kwargs (Dict[str, Any]): A dictionary containing consolidated arguments
                                   (URL path params, query params, JSON body).
                                   Expected keys: 'message' (required), 'title' (optional).

        Returns:
            Response: A Flask Response object indicating success or failure.
        """
        command_name = self.command['name']  # Access command name from the Command object
        logger.info(f"{__file__} - Executing '{command_name}' command with arguments: {kwargs}")

        # --- Argument Validation ---
        required_args = self.command['args_types']  # Access args_types from the Command object
        for arg_def in required_args:
            if arg_def.get('required', False) and arg_def['name'] not in kwargs:
                error_message = f"{__file__} - Missing required argument: '{arg_def['name']}' for command '{command_name}'."
                logger.error(error_message)
                return APIResponse.ErrorResponse(error_message, 400).to_response()

        # --- Execute the command logic (send message to client) ---
        # The 'async' nature means the server doesn't wait for client interaction.
        # It just sends the instruction and returns immediately.
        response_data, status_code = helper_function(**kwargs)

        # --- Return API Response ---
        if status_code != 200:
            logger.error(f"{__file__} - Failed to send message: {response_data}")
            return APIResponse.ErrorResponse(response_data).to_response()
        else:
            logger.info(
                f"{__file__} - Command '{command_name}' executed successfully. Message sent: '{kwargs.get('message')}'")
            return APIResponse.SuccessResponse(
                message=f"Command '{command_name}' executed successfully. Message sent to client for display.",
                data=response_data
            ).to_response()

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the CommandEndpoint instance's command metadata to a dictionary
        for API response. Delegates to the internal Command object's to_dict method.

        Returns:
            Dict[str, Any]: A dictionary containing the command's name, title,
                            description, and arguments.
        """
        # The internal Command object already has a to_dict method
        # that returns the desired structure.
        return self.command.to_dict()


# This is the helper function that simulates sending the message to the client.
# In a real application, this would involve client-specific communication (e.g., WebSockets, polling).
def _send_message_to_client_async(**kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Simulates sending a message to an asynchronous client window.
    This function does NOT wait for user interaction on the client side.

    Args:
        kwargs (Dict[str, Any]): Contains 'message' (str) and optional 'title' (str).

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing the response data and HTTP status code.
                                    The data indicates the action taken.
    """
    message_content = kwargs.get('message')
    window_title = kwargs.get('title', 'Notification')  # Default title if not provided

    if not message_content:
        return {"message": "Message content is required to display a window."}, 400

    # Simulate the action of sending the message to the client.
    # In a real system, this might involve:
    # - Publishing to a message queue (e.g., Redis Pub/Sub, RabbitMQ)
    # - Sending a WebSocket message to the connected client
    # - Updating a database record that the client periodically polls
    logger.debug(f"Simulating sending message to client: Title='{window_title}', Message='{message_content}'")

    # Return success immediately, as the server-side action is complete.
    # The client will handle the actual display asynchronously.
    data = {
        "action": "display_message_window",
        "title": window_title,
        "message_content": message_content,
        "status": "triggered_client_action"
    }
    return data, 200


# Command Registration Function
# This function is called by the main command loader (_load_all_commands in endpoint.py).
def register() -> Tuple[Union[str, CommandEndpoint], int]:
    """
    Registers the 'show_message_window' command with the global command registry.

    Returns:
        Tuple[Union[str, CommandEndpoint], int]: A tuple containing the CommandEndpoint object and 200 on success,
                                                 or an error message string and an HTTP status code on failure.
    """
    # --- Define Command Metadata ---
    command_title = "Show Message Window"
    command_description = "Displays a message in an asynchronous window on the client side without blocking server execution."

    # Define expected arguments for documentation and validation.
    command_args_types: List[Dict[str, Any]] = [
        {
            "name": "message",
            "type": "str",
            "required": True,
            "description": "The text message to be displayed in the client window."
        },
        {
            "name": "title",
            "type": "str",
            "required": False,
            "description": "The title of the message window (defaults to 'Notification')."
        }
    ]

    # Create an instance of the CommandEndpoint class
    command_endpoint_instance = CommandEndpoint(
        title=command_title,
        description=command_description,
        args_types=command_args_types
    )

    return command_endpoint_instance, 200


# This is the helper function that contains the actual logic of the command.
# It now pushes the message to the queue for the Tkinter thread.
def helper_function(**kwargs: Dict[str, Any]) -> Tuple[str, int]:
    """
    Queues the message data for display by the Tkinter thread.
    :param kwargs: Dict[str, Any]: Contains 'message', 'title', 'type', 'timeout_ms' from the request.
    :return: Tuple[str, int]: A status message and HTTP status code indicating if dispatch was successful.
    """
    message_text = kwargs.get("message")
    popup_title = kwargs.get("title", "Notification")
    popup_type = kwargs.get("type", "info")
    timeout_ms = kwargs.get("timeout_ms", 5000)

    # Ensure the Tkinter root exists and the thread is alive before attempting to put
    if _TK_ROOT is None or not _TK_ROOT.winfo_exists():
        logger.error("Tkinter root not initialized or thread not running. Cannot display popup.")
        return "Tkinter GUI not ready.", 500

    try:
        # Prepare the data to be sent to the Tkinter thread
        message_data = {
            "message_text": message_text,
            "popup_title": popup_title,
            "popup_type": popup_type,
            "timeout_ms": timeout_ms,
            "timestamp": datetime.datetime.now().isoformat()
        }
        _MESSAGE_QUEUE.put(message_data)
        logger.info(f"Message '{message_text[:30]}...' successfully queued for Tkinter display.")
        return "Message queued for display.", 200
    except Exception as e:
        logger.error(f"Failed to put message in Tkinter queue: {e}", exc_info=True)
        return f"Failed to queue message: {e}", 500
