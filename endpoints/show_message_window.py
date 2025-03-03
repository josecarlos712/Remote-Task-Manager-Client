# Blueprint for modular API routes
from flask import jsonify

from utils.APIResponse import error_handler, APIResponse
from utils import APIResponse
import tkinter as tk
from tkinter import messagebox


def register(app, path) -> int:
    methods = ['GET']

    app.add_url_rule(
        f'/api/{path}',
        endpoint=path,
        view_func=error_handler(handler),  # Added error handling
        methods=methods
    )

    #Successful import
    return 0


def handler() -> APIResponse:
    #Here goes the function to implement
    # Create the main window
    root = tk.Tk()
    # Set window title
    root.title("Message Window")
    # Set the window size to 100x100 pixels
    root.geometry("100x100")
    # Disable resizing
    root.resizable(False, False)

    # Function to display the message
    def show_message():
        messagebox.showinfo("Message", "Hello, this is a message!")
        root.destroy()  # Close the main window after the message box is closed

    # Create a button that will show the message when clicked
    message_warn_text = tk.Message(text="You received a message!")
    button = tk.Button(root, text="Show Message", command=show_message)
    message_warn_text.pack()
    button.pack(pady=20)

    # Start the main event loop
    root.mainloop()
    # Use APIResponse module for returning responses or errors.
    return jsonify(APIResponse.SuccessResponse("Message delivered successfully").to_dict()), 200


