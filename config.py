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


log_file = "system.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        # Creates a new log file every day and keeps 7 days
        TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)
configuration = Configuration()

# Other
CONFIG_PATH = 'config/programs.json'
VALID_TOKENS = []
