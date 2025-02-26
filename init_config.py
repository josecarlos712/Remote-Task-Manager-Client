import logging
import os
import re

import config


class Configuration:
    def __init__(self, config_path='configuration.ini'):
        self.config_path = config_path
        self.settings = {}
        self.start()

    # This function is executed on the start of the server to check if everything is okay.
    def start(self):
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
        """Retrieves a configuration value with an optional default."""
        return self.settings.get(key, default)

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
