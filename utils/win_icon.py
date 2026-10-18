# -*- coding: utf-8 -*-
"""Set the Windows console/taskbar icon for the client process."""
from __future__ import annotations

import os
import sys


def resolve_app_icon_path() -> str | None:
    import app_paths

    candidates = (
        os.path.join(app_paths.app_dir(), "assets", "app.ico"),
        os.path.join(app_paths.bundle_dir(), "assets", "app.ico"),
    )
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def apply_app_icon() -> None:
    if sys.platform != "win32":
        return
    ico = resolve_app_icon_path()
    if not ico:
        return
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.SendMessageW.restype = wintypes.LPARAM
        kernel32.GetConsoleWindow.restype = wintypes.HWND

        hicon = user32.LoadImageW(None, ico, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not hicon:
            return
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
    except Exception:
        pass
