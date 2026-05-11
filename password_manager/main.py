import sys
import os

# Ensure package root is on sys.path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from core import database, encryption
from ui.master_password_dialog import MasterPasswordDialog
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VaultMind")
    app.setOrganizationName("VaultMind")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    app.setStyle("Fusion")

    _docs = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    app_icon = QIcon()
    app_icon.addFile(os.path.join(_docs, "icon-1.png"))  # 32x32 — title bar / taskbar
    app_icon.addFile(os.path.join(_docs, "icon-0.png"))  # 48x48 — large icons / Alt+Tab
    app.setWindowIcon(app_icon)

    database.initialize_db()

    first_launch = database.is_first_launch()
    dlg = MasterPasswordDialog(is_first_launch=first_launch)
    if dlg.exec_() != dlg.Accepted:
        sys.exit(0)

    master_password = dlg.master_password

    if first_launch:
        salt = encryption.generate_salt()
        pwd_hash = encryption.hash_password(master_password, salt)
        database.store_master_credentials(salt, pwd_hash)
    else:
        salt, stored_hash = database.get_master_credentials()
        if not encryption.verify_password(master_password, salt, stored_hash):
            QMessageBox.critical(None, "Wrong Password", "Incorrect master password. Exiting.")
            sys.exit(1)

    enc_key = encryption.derive_key(master_password, salt)

    window = MainWindow(enc_key)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
