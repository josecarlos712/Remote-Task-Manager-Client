import re
import os
import logging
from typing import Dict, Any, Union
from logging.handlers import TimedRotatingFileHandler

LOGGING_LEVEL = logging.DEBUG  # Set the default logging level


class Configuration:
    def __init__(self, config_path='config/'
                                   'configuration.ini'):
        self._system_info = {}
        self.logging = None
        self.config_path = config_path
        self._settings = {}
        self.start()

    # This function is executed on the start of the server to check if everything is okay.
    def start(self):
        self.logging_configuration()
        # There can't be any logging until the logging initialization
        self.load_specifications()
        self.read_configuration()
        self.logging.debug(f"Configuration loaded successfully. {self._settings}")
        self.check_files()

    def logging_configuration(self) -> logging:
        log_file = "logs/system.log"
        logging.basicConfig(
            level=LOGGING_LEVEL,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                # Creates a new log file every day and keeps 7 days
                TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
            ]
        )
        self.logging: logging = logging.getLogger(__name__)

    def load_specifications(self):
        import os
        import socket
        import json
        import platform
        import uuid
        import psutil
        import requests
        import subprocess

        system_info_path = "logs/system_info.json"
        self._system_info = {}

        # In the specifications file there is a list of static values of the client (name, local ip, etc)
        def get_system_info() -> dict:
            """Gather all the info from the guest computer and store it on system_info.json"""
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
                output = subprocess.check_output(
                    "wmic cpu get name", shell=True
                ).decode().strip().split("\n")[1:]  # Ignore the header row
                cpu_name = output[0].strip() if output else "Unknown"

                system_info.update({
                    "cpu": cpu_name,
                    "cpu_cores": os.cpu_count(),
                    "ram_size_mb": psutil.virtual_memory().total // (1024 ** 2),
                    "disk_size_gb": psutil.disk_usage('/').total // (1024 ** 3)
                })

                # GPU Info (Windows)
                if platform.system() == "Windows":
                    try:
                        output = subprocess.check_output(
                            "wmic path win32_videocontroller get caption", shell=True
                        ).decode().strip().split("\n")[1:]  # Ignore the header row

                        # Clean up output and filter empty/virtual entries
                        gpus = [gpu.strip() for gpu in output if gpu.strip() and "virtual" not in gpu.lower()]

                        system_info["gpu"] = gpus[0] if gpus else "Unknown"  # Return the first valid GPU found
                    except Exception:
                        system_info["gpu"] = "Unknown"

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
                            subprocess.check_output("wmic bios get smbiosbiosversion",
                                                    shell=True).decode().strip().split(
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

        def save_system_info(filename=system_info_path) -> dict:
            info = get_system_info()
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(info, file, indent=4)
                file.close()
            return info

        # Run the function to save the info
        if not os.path.exists(system_info_path):
            self.logging.log(logging.DEBUG, f"No system_info.json file. Creating one.")

        self._system_info = save_system_info()
        return self._system_info

    def read_configuration(self) -> tuple[Dict[str, Dict[str, Any]] | str, int]:
        """
        Reads a configuration file in INI format and returns its contents as a dictionary.
        It attempts to parse values to appropriate Python types (int, bool, float)
        where possible. Section and option names are automatically converted to lowercase.

        Args:
            file_path (str): The path to the INI configuration file.

        Returns:
            Dict[str, Dict[str, Any]]: A nested dictionary where top-level keys are
                                       section names (lowercase) and values are dictionaries
                                       of options (lowercase) and their parsed values.
                                       Returns an empty dictionary if the file cannot be read
                                       or if an error occurs during parsing.

            or str: An error message if the file cannot be read or parsed.

            int: HTTP status code indicating the result of the operation.
        """
        import configparser
        from config.config import configuration_path

        configparser = configparser.ConfigParser()
        parsed_settings: Dict[str, Dict[str, Any]] = {}
        file_path = configuration_path

        try:
            # config.read() returns a list of successfully parsed filenames.
            # If the list is empty, the file was not found or could not be read.
            if not configparser.read(file_path):
                logging.error(f"Configuration file not found or could not be read: '{file_path}'")
                return f"Configuration file not found or could not be read: '{file_path}'", 404  # Not Found

            # Iterate through each section in the configuration
            for section in configparser.sections():
                parsed_settings[section] = {}  # Initialize dictionary for the current section
                # Iterate through each key-value pair within the section
                for key, value_str in configparser.items(section):
                    # Attempt to convert string values to Python types
                    try:
                        # 1. Try converting to boolean (case-insensitive 'true'/'false')
                        if value_str.lower() in ('true', 'false'):
                            parsed_settings[section][key] = configparser.getboolean(section, key)
                        # 2. Try converting to integer
                        elif value_str.strip().isdigit() or (
                                value_str.strip().startswith('-') and value_str.strip()[1:].isdigit()):
                            parsed_settings[section][key] = configparser.getint(section, key)
                        # 3. Try converting to float (handles decimals)
                        elif '.' in value_str and (value_str.replace('.', '', 1).strip().isdigit() or (
                                value_str.strip().startswith('-') and value_str[1:].replace('.', '',
                                                                                            1).strip().isdigit())):
                            parsed_settings[section][key] = configparser.getfloat(section, key)
                        # 4. Default to string if no other type matches
                        else:
                            parsed_settings[section][key] = value_str.strip()
                    except ValueError:
                        # If built-in parsers fail (e.g., trying to parse "0.0.0.0" as float),
                        # keep the value as a string.
                        logging.warning(
                            f"Could not automatically parse '{key}' in section '{section}' (value: '{value_str}'). Storing as string.")
                        parsed_settings[section][key] = value_str.strip()
            self._settings = parsed_settings

        except configparser.Error as e:
            # Catch specific errors from configparser (e.g., malformed INI syntax)
            logging.error(f"Error parsing configuration file '{file_path}': {e}")
            return f"Error parsing configuration file '{file_path}': {e}", 400  # Bad Request
        except Exception as e:
            # Catch any other unexpected errors
            logging.error(f"An unexpected error occurred while reading configuration file '{file_path}': {e}",
                          exc_info=True)
            return f"An unexpected error occurred while reading configuration file '{file_path}': {e}", 500  # Internal Server Error

    def parse_value(self, value_str) -> Union[str, int, float, bool]:
        """Converts string values to appropriate data types."""
        ...

    def get_specification_info(self, key_path):
        """This is a get function for the computer speficications.

        This get function uses a nested key path with the format 'key.subkey.subsubkey'"""
        keys = key_path.split(".")  # Support dot notation for nested keys
        value = self._system_info

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]  # Go deeper into the dictionary
            else:
                return None  # Key not found

        return value

    def check_files(self):
        """Check for important directories and files inside the proyect."""
        import os
        # Checking downloads
        downloads_folder = self["paths"]["path_downloads"]
        if not downloads_folder:
            self.logging.log(logging.ERROR, "CheckFiles ERROR: 'path_downloads' is not defined in the configuration.")
            return
        # Ensure the downloads folder exists
        downloads_folder_absolute = os.path.expanduser(downloads_folder)
        if not os.path.isabs(downloads_folder_absolute):
            downloads_folder_absolute = os.path.join(os.getcwd(), downloads_folder)
        if not os.path.exists(downloads_folder_absolute):
            self.logging.log(logging.WARNING,
                             f"CheckFiles WARNING: Downloads folder '{downloads_folder_absolute}' does not exist. Creating it.")
            try:
                os.makedirs(downloads_folder_absolute, exist_ok=True)
            except Exception as e:
                self.logging.log(logging.ERROR, f"CheckFiles ERROR: Exception on os.makedirs - {e}")

        self.logging.log(logging.DEBUG, "CheckFiles OK")

    # To get a specific value from the configuration file or the system info
    def __getitem__(self, key: str) -> Union[Dict[str, Any], Any]:
        """
        Allows accessing configuration sections and options using dictionary-like syntax.
        e.g., config["server settings"] to get a section dictionary,
        or config["paths"]["path_downloads"] to get a specific value.

        Args:
            key (str): The name of the section or option to retrieve.

        Returns:
            Union[Dict[str, Any], Any]: A dictionary representing a section, or the value of an option.

        Raises:
            KeyError: If the specified key (section or option) does not exist.
        """
        if key not in self._settings:
            raise KeyError(f"Configuration key or section '{key}' not found.")
        return self._settings[key]
