import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler

import config


class Configuration:
    def __init__(self, config_path='configuration.ini'):
        self.specifications = None
        self.logger = None
        self.config_path = config_path
        self.settings = {}
        self.start()

    # This function is executed on the start of the server to check if everything is okay.
    def start(self):
        self.load_specifications()
        self.logging_configuration()
        self.load_config()
        self.check_files()

    def load_config(self):
        """Loads the configuration file and parses key-value pairs."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file '{self.config_path}' not found.")

        with open(self.config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    key, value = map(str.strip, line.split("=", 1))
                    self.settings[key] = self.parse_value(value)

    def logging_configuration(self) -> logging:
        log_file = "logs/system.log"
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                # Creates a new log file every day and keeps 7 days
                TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
            ]
        )
        self.logger = logging.getLogger(__name__)

        return self.logger

    def load_specifications(self):
        # In the specifications file there is a list of static values of the client (name, local ip, etc)
        self.specifications = None

        import os
        import socket
        import json
        import platform
        import uuid
        import psutil
        import requests
        import subprocess

        def get_system_info():
            try:
                # Basic System Info
                system_info = {
                    "computer_name": socket.gethostname(),
                    "local_ip": socket.gethostbyname(socket.gethostname()),
                    "mac_address": ':'.join(f"{(uuid.getnode() >> i) & 0xff:02x}" for i in range(0, 48, 8)),
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "os_release": platform.release(),
                    "os_architecture": platform.architecture()[0],
                    "user_name": os.getlogin(),
                    "domain_name": os.getenv("USERDOMAIN", "Unknown")
                }

                # Hardware Info
                system_info.update({
                    "cpu": platform.processor(),
                    "cpu_cores": os.cpu_count(),
                    "ram_size_gb": psutil.virtual_memory().total // (1024 ** 3),
                    "disk_size_gb": psutil.disk_usage('/').total // (1024 ** 3)
                })

                # GPU Info (Windows)
                if platform.system() == "Windows":
                    try:
                        gpu_info = subprocess.check_output("wmic path win32_videocontroller get caption",
                                                           shell=True).decode().strip().split("\n")[1].strip()
                    except Exception:
                        gpu_info = "Unknown"
                    system_info["gpu"] = gpu_info

                # Public IP
                try:
                    system_info["public_ip"] = requests.get("https://api64.ipify.org", timeout=3).text
                except requests.RequestException:
                    system_info["public_ip"] = "Unknown"

                # Network Info (Windows)
                if platform.system() == "Windows":
                    try:
                        net_info = subprocess.check_output("ipconfig /all", shell=True).decode()
                        dns_servers = [line.split(":")[-1].strip() for line in net_info.split("\n") if
                                       "DNS Servers" in line]
                        system_info["dns_servers"] = dns_servers
                    except Exception:
                        system_info["dns_servers"] = []

                # BIOS & Motherboard Info (Windows)
                if platform.system() == "Windows":
                    try:
                        bios_version = \
                        subprocess.check_output("wmic bios get smbiosbiosversion", shell=True).decode().strip().split(
                            "\n")[1].strip()
                        system_info["bios_version"] = bios_version
                    except Exception:
                        system_info["bios_version"] = "Unknown"

                    try:
                        motherboard = subprocess.check_output("wmic baseboard get product,manufacturer",
                                                              shell=True).decode().strip().split("\n")[1].strip()
                        system_info["motherboard"] = motherboard
                    except Exception:
                        system_info["motherboard"] = "Unknown"

                return system_info
            except Exception as e:
                return {"error": f"Failed to gather system info: {str(e)}"}

        def save_system_info(filename="system_info.json"):
            info = get_system_info()
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(info, file, indent=4)

        # Run the function to save the info
        save_system_info()

    def parse_value(self, value):
        """Converts string values to appropriate data types."""
        if value.lower() in ['true', 'false']:  # Boolean conversion
            return value.lower() == 'true'
        elif value.isdigit():  # Integer conversion
            return int(value)
        elif value.replace('.', '', 1).isdigit():  # Float conversion
            return float(value)
        return value  # Default to string

    def get(self, key, default=None):
        """Retrieves a configuration value given the key."""
        return self.settings.get(key, default)

    def get_info(self, key_path):
        """This is a get function for the computer speficications.

        This get function uses a nested key path with the format 'key.subkey.subsubkey'"""
        keys = key_path.split(".")  # Support dot notation for nested keys
        value = self.specifications

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]  # Go deeper into the dictionary
            else:
                return None  # Key not found

        return value

    def check_files(self):
        """Check for important directories and files inside the proyect."""
        #Checking downloads
        is_absolute_path = bool(re.match(r"^[A-Za-z]:[\\/]", self.settings.get("PATH_DOWNLOADS")))
        downloads_folder = os.path.join(os.getcwd(), "downloads") if is_absolute_path else self.settings.get("PATH_DOWNLOADS")
        try:
            os.makedirs(downloads_folder, exist_ok=True)
        except Exception as e:
            logging.log(config.LogLevel.ERROR.value, f"CheckFiles ERROR: Exception on os.makedirs - {e}")
        logging.log(config.LogLevel.DEBUG.value, "CheckFiles OK")
