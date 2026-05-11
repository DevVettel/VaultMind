from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.utils import apply_dark_titlebar


STYLE = """
QDialog {
    background-color: #1e1e2e;
    color: #e2e8f0;
}
QLabel {
    color: #e2e8f0;
    font-size: 15px;
}
QLabel#title {
    font-size: 28px;
    font-weight: bold;
    color: #5b8dee;
}
QLabel#subtitle {
    font-size: 14px;
    color: #94a3b8;
}
QLineEdit {
    background-color: #2a2a3e;
    color: #e2e8f0;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 15px;
}
QLineEdit:focus {
    border: 1px solid #072182;
}
QPushButton#primary {
    background-color: #072182;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #0a2fa0;
}
QPushButton#primary:pressed {
    background-color: #051868;
}
"""


class MasterPasswordDialog(QDialog):
    def __init__(self, is_first_launch: bool, parent=None):
        super().__init__(parent)
        self.is_first_launch = is_first_launch
        self.master_password = None
        self._build_ui()
        self.setStyleSheet(STYLE)

    def _build_ui(self):
        self.setWindowTitle("VaultMind — Master Password")
        self.setFixedSize(500, 545 if self.is_first_launch else 320)
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)

        title = QLabel("VaultMind")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        if self.is_first_launch:
            sub = QLabel("Set up your master password to protect your vault.")
        else:
            sub = QLabel("Enter your master password to unlock your vault.")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        layout.addWidget(sub)

        if self.is_first_launch:
            info = QFrame()
            info.setStyleSheet(
                "QFrame { background-color: #0b1a3d; border: 1px solid #1a3570; border-radius: 6px; }"
            )
            il = QVBoxLayout(info)
            il.setContentsMargins(16, 12, 16, 12)
            il.setSpacing(6)

            heading = QLabel("Your master password is the key to your vault.")
            heading.setStyleSheet("color: #5b8dee; font-size: 13px; font-weight: bold; border: none;")
            heading.setWordWrap(True)
            il.addWidget(heading)

            body = QLabel(
                "It encrypts and protects all stored credentials — "
                "without it, your data cannot be recovered."
            )
            body.setStyleSheet("color: #94a3b8; font-size: 13px; border: none;")
            body.setWordWrap(True)
            il.addWidget(body)

            for bullet in (
                "Never shared or stored — only you know it.",
                "Cannot be reset or recovered if forgotten.",
                "Must be at least 8 characters long.",
            ):
                lbl = QLabel(f"  •  {bullet}")
                lbl.setStyleSheet("color: #94a3b8; font-size: 13px; border: none;")
                lbl.setWordWrap(True)
                il.addWidget(lbl)

            note = QLabel("Choose a strong, memorable password and keep it safe.")
            note.setStyleSheet(
                "color: #e2e8f0; font-size: 12px; font-style: italic; border: none;"
            )
            note.setWordWrap(True)
            il.addWidget(note)

            layout.addWidget(info)

        layout.addSpacing(6)

        pw_label = QLabel("Master Password")
        layout.addWidget(pw_label)

        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Enter master password...")
        layout.addWidget(self.pw_input)

        if self.is_first_launch:
            confirm_label = QLabel("Confirm Password")
            layout.addWidget(confirm_label)

            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirm master password...")
            layout.addWidget(self.confirm_input)
            self.confirm_input.returnPressed.connect(self._submit)

        layout.addSpacing(4)

        btn = QPushButton("Unlock Vault" if not self.is_first_launch else "Create Vault")
        btn.setObjectName("primary")
        btn.clicked.connect(self._submit)
        layout.addWidget(btn)

        self.pw_input.returnPressed.connect(self._submit)

    def _submit(self):
        password = self.pw_input.text()
        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return

        if self.is_first_launch:
            confirm = self.confirm_input.text()
            if password != confirm:
                QMessageBox.warning(self, "Error", "Passwords do not match.")
                return
            if len(password) < 8:
                QMessageBox.warning(self, "Error", "Master password must be at least 8 characters.")
                return

        self.master_password = password
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)
