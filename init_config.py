import os
import config


class Config:
    def __init__(self, config_path='configuration.ini'):
        self.config_path = config_path
        self.settings = {}
        self.load_config()

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