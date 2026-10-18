import base64
import io
import os
from datetime import datetime

from config import logger

COMMAND_ID = "screenshot"
TITLE = "Take Screenshot"
DESCRIPTION = "Captures the primary screen and returns a PNG as base64 (also saved under downloads/)."
ARGS = [
    {
        "name": "save_only",
        "type": "bool",
        "required": False,
        "description": "If true, only save to disk and return the path.",
    }
]


def handler(**kwargs):
    try:
        from PIL import ImageGrab
    except ImportError:
        return "Pillow is required for screenshots (pip install Pillow).", 501

    save_only = bool(kwargs.get("save_only", False))
    image = ImageGrab.grab()
    os.makedirs("downloads", exist_ok=True)
    filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
    path = os.path.join("downloads", filename)
    image.save(path, format="PNG")
    logger.info(f"screenshot saved to {path}")

    if save_only:
        return {"path": path}, 200

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"path": path, "png_base64": encoded}, 200
