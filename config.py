import logging
import os
import secrets
from enum import Enum

from init_config import Configuration


class LogLevel(Enum):
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0


configuration = Configuration()
logger = configuration.logging

CONFIG_PATH = "config/programs.json"
VALID_TOKENS = {}

# In-memory API key (can be updated after register response)
_api_key_override = None


def get_setting(key: str, default=None):
    try:
        value = configuration[key]
        return default if value is None else value
    except Exception:
        return default


def get_server_url() -> str:
    return str(get_setting("server_url", "http://127.0.0.1:8000")).rstrip("/")


def get_register_token() -> str:
    return str(get_setting("register_token", "") or os.environ.get("CLIENT_REGISTER_TOKEN", ""))


def get_owner_username() -> str:
    return str(get_setting("owner_username", "") or "")


def get_client_name() -> str:
    name = get_setting("client_name")
    if name:
        return str(name)
    return str(configuration.get_specification_info("computer_name") or "client")


def get_local_ip() -> str:
    return str(configuration.get_specification_info("local_ip") or "127.0.0.1")


def get_port() -> int:
    return int(get_setting("port", 5000))


def get_health_interval() -> int:
    return int(get_setting("health_interval", 60))


def get_api_key() -> str:
    global _api_key_override
    if _api_key_override:
        return str(_api_key_override)
    env_key = os.environ.get("CLIENT_API_KEY")
    if env_key:
        return str(env_key)
    configured = get_setting("api_key", "") or ""
    return str(configured).strip()


def set_api_key(api_key: str, persist: bool = True) -> None:
    """Store API key in memory and persist it to configuration.ini by default."""
    global _api_key_override
    api_key = (api_key or "").strip()
    if not api_key:
        logger.warning("set_api_key() called with empty key; ignoring.")
        return
    _api_key_override = api_key
    if persist:
        try:
            configuration.set_and_persist("api_key", api_key)
            logger.info("Client API key saved to configuration.ini")
        except Exception as e:
            logger.error(f"Could not persist API key to configuration.ini: {e}")
    else:
        logger.info("Client API key updated in memory only.")


def ensure_api_key() -> str:
    """Return existing API key or generate+persist a new one."""
    current = get_api_key()
    if current:
        return current
    generated = secrets.token_hex(32)
    set_api_key(generated, persist=True)
    logger.info("Generated new client API key.")
    return generated
