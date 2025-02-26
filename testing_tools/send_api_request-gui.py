import tkinter as tk
from tkinter import scrolledtext
import requests
import json

def send_request():
    command = command_entry.get()
    message = message_entry.get()
    port = port_entry.get()
    
    # Clear previous response
    response_text.delete(1.0, tk.END)
    
    if not port:
        response_text.insert(tk.END, "Error: El campo 'port' es obligatorio.")
        return
    if not command:
        response_text.insert(tk.END, "Error: El campo 'command' es obligatorio.")
        return
    
    url = f"http://localhost:{port}/api/command"
    payload = {"command": command, "message": message}
    
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        formatted_response = json.dumps(response_data, indent=4)
        response_text.insert(tk.END, formatted_response)
    except requests.exceptions.RequestException as e:
        response_text.insert(tk.END, f"Error en la solicitud: {e}")

# Configuración de la ventana
root = tk.Tk()
root.title("JSON Request Sender")
root.geometry("400x500")
root.resizable(True, True)  # Allow window resizing

# Create main frame
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Input fields frame
input_frame = tk.Frame(main_frame)
input_frame.pack(fill=tk.X, pady=5)

# Port input
port_label = tk.Label(input_frame, text="Port:")
port_label.pack()
port_entry = tk.Entry(input_frame)
port_entry.pack(fill=tk.X)
port_entry.insert(0, "5000")

# Command input
command_label = tk.Label(input_frame, text="Command:")
command_label.pack()
command_entry = tk.Entry(input_frame)
command_entry.pack(fill=tk.X)

# Message input
message_label = tk.Label(input_frame, text="Message:")
message_label.pack()
message_entry = tk.Entry(input_frame)
message_entry.pack(fill=tk.X)

# Send button
send_button = tk.Button(input_frame, text="Send Request", command=send_request)
send_button.pack(pady=10)

# Response frame
response_frame = tk.Frame(main_frame)
response_frame.pack(fill=tk.BOTH, expand=True)

# Response label
response_label = tk.Label(response_frame, text="Server Response:")
response_label.pack()

# Response text area
response_text = scrolledtext.ScrolledText(response_frame)
response_text.pack(fill=tk.BOTH, expand=True)

root.mainloop()