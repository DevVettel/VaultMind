"""Locate bundled assets both from a source checkout and a PyInstaller build."""
import os
import sys

_ROOT = getattr(sys, "_MEIPASS", None) or os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)

ICON_SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)


def asset_path(*parts: str) -> str:
    return os.path.join(_ROOT, "assets", *parts)


def qss_url(*parts: str) -> str:
    """Path usable inside a Qt stylesheet `url(...)` (forward slashes on Windows too)."""
    return asset_path(*parts).replace(os.sep, "/")
