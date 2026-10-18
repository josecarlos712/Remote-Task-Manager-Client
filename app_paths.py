# -*- coding: utf-8 -*-
"""Resolve application root for source runs and frozen (PyInstaller) builds."""
from __future__ import annotations

import os
import sys


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    """PyInstaller extract dir, or app_dir when running from source."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return str(sys._MEIPASS)
    return app_dir()


def ensure_runtime_cwd() -> str:
    """Make relative paths (configuration.ini, config/, logs/) resolve next to the exe."""
    root = app_dir()
    try:
        os.chdir(root)
    except OSError:
        pass
    if root not in sys.path:
        sys.path.insert(0, root)
    return root
