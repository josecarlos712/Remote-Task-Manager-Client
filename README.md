# Remote Task Manager (RTM)

**Remote Task Manager** is a modular ecosystem designed to centralize the control of multiple devices within a local network. This project eliminates the technical barrier of managing different operating systems and devices individually, transforming complex operations into direct actions through a web interface.

-----

## ✨ Main Features

  * **Command Abstraction:** Execute terminal operations using intuitive buttons within the interface.
  * **Modular Architecture:** Based on a blueprint system, it allows adding new functionalities without modifying the core code.
  * **Responsive Interface:** Full control from desktop browsers or mobile devices.
  * **Security and Control:** Access management via API Keys and device assignment to specific owners.
  * **Multi-device:** Capability to manage PCs, servers, and other devices with Python installed.

-----

## 🖼️ Screenshots

\<p align="center"\>
\<img src="screenshots/login.png" width="32%" alt="Login"\>
\<img src="screenshots/dashboard.png" width="32%" alt="Dashboard"\>
\<img src="screenshots/acciones.png" width="32%" alt="Remote Actions"\>
\</p\>

-----

## 🛠️ System Possibilities

The system is extensible by design, allowing the implementation of:

  * **Power Control:** Shutdown, restart, and sleep.
  * **Monitoring:** Real-time screenshots and system status.
  * **File Management:** File transfer between client and server.
  * **Messaging:** Activity system and notifications between users.

-----

## 🏗️ Project Structure

The project is divided into two independent components:

1.  **Server (Django):** The central control panel that manages the database, users, and business logic.
2.  **Client (Python/Flask):** A lightweight application that resides on remote devices and executes received orders.

-----

## ⚙️ Setup and Configuration

### 1\. Prerequisites

  * 🐍 **Python 3.10** or higher.
  * 🌐 **Network Connection:** Devices must be visible to each other within the local network.

### 2\. Server Configuration (Control Panel)

Execute these commands on the machine that will act as the central server:

```bash
cd Remote-Task-Server
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 3\. Client Configuration (Remote Agent)

Execute these commands on each device you wish to control:

```bash
cd Remote-Task-Client
pip install -r requirements.txt
python main.py
```

-----

## 📄 Credits

Project developed by **José Carlos Crespo Falcón** as a Bachelor's Thesis in Computer Engineering (Computer Engineering), University of Seville, academic year 2024/25.
