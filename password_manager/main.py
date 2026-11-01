import os
import sys

# Ensure package root is on sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from core import database, vault
from resources import ICON_SIZES, asset_path
from ui.main_window import MainWindow
from ui.master_password_dialog import MasterPasswordDialog
from version import __version__


def _app_icon() -> QIcon:
    """Multi-resolution app icon so Qt picks a sharp bitmap for every context
    (title bar, taskbar, Alt+Tab, macOS Dock on Retina displays)."""
    icon = QIcon()
    for size in ICON_SIZES:
        path = asset_path("icons", f"icon-{size}.png")
        if os.path.exists(path):
            icon.addFile(path, QSize(size, size))
    return icon


def _default_ui_font() -> QFont:
    if sys.platform == "darwin":
        families = [".AppleSystemUIFont", "SF Pro Text", "Helvetica Neue"]
    elif sys.platform == "win32":
        families = ["Segoe UI"]
    else:
        families = ["Ubuntu", "Cantarell", "DejaVu Sans"]

    font = QFont(families[0], 10)
    font.setFamilies(families)
    return font


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VaultMind")
    app.setOrganizationName("VaultMind")
    app.setApplicationVersion(__version__)

    app.setFont(_default_ui_font())

    app.setStyle("Fusion")

    app.setWindowIcon(_app_icon())

    database.initialize_db()

    first_launch = vault.is_first_launch()
    dlg = MasterPasswordDialog(
        is_first_launch=first_launch,
        unlock=vault.create_vault if first_launch else vault.unlock_vault,
    )
    if dlg.exec_() != dlg.Accepted:
        sys.exit(0)

    window = MainWindow(dlg.enc_key)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
