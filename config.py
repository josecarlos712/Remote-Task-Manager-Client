import logging
from enum import Enum
from logging.handlers import TimedRotatingFileHandler

from init_config import Configuration


# IMPROVEMENT: Added structured logging configuration
# Configure logging
class LogLevel(Enum):
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0


configuration = Configuration() #Init for Configuration
logger = configuration.logger #Make the logger global

# Other
CONFIG_PATH = 'config/programs.json'
VALID_TOKENS = []
