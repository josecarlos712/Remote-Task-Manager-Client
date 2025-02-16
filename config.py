import logging
from logging.handlers import TimedRotatingFileHandler

# IMPROVEMENT: Added structured logging configuration
# Configure logging
log_file = "system.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        # Creates a new log file every day and keeps 7 days
        TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)
CONFIG_PATH = 'config/programs.json'
VALID_TOKENS = []
