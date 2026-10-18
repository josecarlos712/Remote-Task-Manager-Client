import webbrowser

from config import logger

COMMAND_ID = "open_url"
TITLE = "Open URL"
DESCRIPTION = "Opens a URL in the default browser on the client."
ARGS = [
    {
        "name": "url",
        "type": "str",
        "required": True,
        "description": "URL to open (http/https).",
    }
]


def handler(**kwargs):
    url = kwargs.get("url")
    if not url or not isinstance(url, str):
        return "Missing required argument: url", 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return "URL must start with http:// or https://", 400
    logger.info(f"open_url opening {url}")
    webbrowser.open(url)
    return f"Opened {url}", 200
