# Remote Task Client

This project corresponds to the **client** component of a client-server system developed as a Bachelor's Thesis (TFG). It listens for instructions from the server and executes them on the local machine.

## ⚙️ Features

- Listens for commands from the server on a local network.
- Executes commands defined as modular plugins.
- Communication based on JSON.
- Supports various commands:
  - Shut down the system.
  - Display pop-up messages.
  - Take screenshots.
  - Download files.
  - Run local scripts.

## 🧩 Modular Architecture

Each command is an importable function that can be dynamically registered, allowing easy extension without modifying the main client logic.

````

remote-task-client/
├── commands/           # Individual command modules
│   ├── **init**.py
│   └── shutdown.py, popup.py, ...
├── main.py             # Client main logic
├── communication.py    # Communication with the server
└── utils/              # Helper functions

````

## 🚀 Running the Project

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
````

2. Run the client:

```bash
python main.py
```

The client will remain active and wait for incoming tasks.

## 🔧 Configuration

Edit the `config.py` file or use environment variables to specify:

* Server address
* Port
* Authentication token (if applicable)

## 🛠️ Available Commands

| Name        | Description                      |
| ----------- | -------------------------------- |
| shutdown    | Shuts down the remote system     |
| popup       | Displays a popup message         |
| screenshot  | Takes a screenshot of the client |
| download    | Downloads files from URLs        |
| run\_script | Executes a local script          |

## 🚨 Security

* The client only responds to authenticated requests.
* Each command includes parameter validation.
* Intended for use in trusted LAN environments.

## 📌 Development Status

✅ Modular command system
✅ Communication with server
✅ Basic remote control
❌ Data encryption
❌ Detailed logging
❌ Auto-updates

## 📄 License

MIT License