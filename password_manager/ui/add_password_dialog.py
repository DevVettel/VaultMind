from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSlider, QCheckBox, QFrame,
    QProgressBar, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.password_generator import generate_password, password_strength
from ui.utils import apply_dark_titlebar


CATEGORIES = ["General", "Email", "Social", "Banking", "Work", "Shopping", "Other"]

STYLE = """
QDialog {
    background-color: #1e1e2e;
    color: #e2e8f0;
}
QLabel {
    color: #e2e8f0;
    font-size: 14px;
}
QLabel#dialog_title {
    font-size: 20px;
    font-weight: bold;
    color: #5b8dee;
}
QLineEdit, QComboBox {
    background-color: #2a2a3e;
    color: #e2e8f0;
    border: 1px solid #3d3d5c;
    border-radius: 5px;
    padding: 9px 12px;
    font-size: 14px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #072182;
}
QLineEdit#mono {
    font-family: Consolas, monospace;
    font-size: 15px;
    letter-spacing: 1px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #2a2a3e;
    color: #e2e8f0;
    selection-background-color: #072182;
    selection-color: #ffffff;
    border: 1px solid #3d3d5c;
    outline: none;
    font-size: 14px;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    color: #e2e8f0;
    background-color: #2a2a3e;
    min-height: 28px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #3d3d5c;
    color: #e2e8f0;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #072182;
    color: #ffffff;
}
QPushButton {
    background-color: #2a2a3e;
    color: #e2e8f0;
    border: 1px solid #3d3d5c;
    border-radius: 5px;
    padding: 9px 16px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #3d3d5c;
}
QPushButton#primary {
    background-color: #072182;
    color: white;
    border: none;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #0a2fa0;
}
QPushButton#icon_btn {
    background-color: transparent;
    border: none;
    padding: 4px 8px;
    color: #94a3b8;
    font-size: 16px;
}
QPushButton#icon_btn:hover {
    color: #5b8dee;
}
QCheckBox {
    color: #94a3b8;
    font-size: 13px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #3d3d5c;
    background-color: #2a2a3e;
}
QCheckBox::indicator:checked {
    background-color: #072182;
    border-color: #072182;
}
QSlider::groove:horizontal {
    height: 4px;
    background: #3d3d5c;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #072182;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #072182;
    border-radius: 2px;
}
QProgressBar {
    border: none;
    border-radius: 5px;
    background-color: #2a2a3e;
    min-height: 24px;
    max-height: 24px;
    text-align: center;
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}
QProgressBar::chunk {
    border-radius: 5px;
}
QFrame#separator {
    background-color: #3d3d5c;
    max-height: 1px;
}
"""


class AddPasswordDialog(QDialog):
    def __init__(self, encryption_key: bytes, record=None, parent=None):
        super().__init__(parent)
        self.encryption_key = encryption_key
        self.record = record
        self.result_data = None
        self._build_ui()
        self.setStyleSheet(STYLE)

        if record:
            self._populate(record)

    def _build_ui(self):
        title_text = "Edit Password" if self.record else "Add Password"
        self.setWindowTitle(f"VaultMind — {title_text}")
        self.setFixedWidth(540)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title_lbl = QLabel(title_text)
        title_lbl.setObjectName("dialog_title")
        layout.addWidget(title_lbl)

        layout.addWidget(self._sep())

        # Title
        layout.addWidget(QLabel("Title *"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Gmail, Netflix...")
        layout.addWidget(self.title_input)

        # Username
        layout.addWidget(QLabel("Username / Email *"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. user@example.com")
        layout.addWidget(self.username_input)

        # Password row
        layout.addWidget(QLabel("Password *"))
        pw_row = QHBoxLayout()
        pw_row.setSpacing(6)
        self.pw_input = QLineEdit()
        self.pw_input.setObjectName("mono")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Enter or generate password...")
        self.pw_input.textChanged.connect(self._update_strength)
        pw_row.addWidget(self.pw_input)

        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setObjectName("icon_btn")
        self.toggle_btn.setFixedWidth(36)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self._toggle_visibility)
        pw_row.addWidget(self.toggle_btn)

        gen_btn = QPushButton("Generate")
        gen_btn.clicked.connect(self._open_generator)
        pw_row.addWidget(gen_btn)
        layout.addLayout(pw_row)

        # Strength bar
        strength_row = QHBoxLayout()
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(True)
        strength_row.addWidget(self.strength_bar)
        self.strength_label = QLabel("—")
        self.strength_label.setFixedWidth(70)
        self.strength_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.strength_label.setContentsMargins(10, 0, 0, 0)
        strength_row.addWidget(self.strength_label)
        layout.addLayout(strength_row)

        # Category
        layout.addWidget(QLabel("Category"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.view().setStyleSheet(
            "QAbstractItemView {"
            "  background-color: #2a2a3e;"
            "  color: #e2e8f0;"
            "  selection-background-color: #072182;"
            "  selection-color: #ffffff;"
            "  border: 1px solid #3d3d5c;"
            "  outline: none;"
            "}"
            "QAbstractItemView::item {"
            "  padding: 8px 12px;"
            "  min-height: 28px;"
            "  background-color: #2a2a3e;"
            "  color: #e2e8f0;"
            "}"
            "QAbstractItemView::item:hover {"
            "  background-color: #3d3d5c;"
            "}"
            "QAbstractItemView::item:selected {"
            "  background-color: #072182;"
            "  color: #ffffff;"
            "}"
        )
        layout.addWidget(self.category_combo)

        layout.addWidget(self._sep())

        # Generator options (collapsed by default, shown inline)
        self.gen_frame = self._build_generator_frame()
        self.gen_frame.setVisible(False)
        layout.addWidget(self.gen_frame)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Password")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _sep(self):
        f = QFrame()
        f.setObjectName("separator")
        f.setFrameShape(QFrame.HLine)
        return f

    def _build_generator_frame(self):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #252535; border-radius: 6px; }")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(14, 12, 14, 12)
        fl.setSpacing(10)

        lbl = QLabel("Password Generator")
        lbl.setStyleSheet("font-weight: bold; color: #a78bfa;")
        fl.addWidget(lbl)

        # Length slider
        len_row = QHBoxLayout()
        len_row.addWidget(QLabel("Length:"))
        self.len_slider = QSlider(Qt.Horizontal)
        self.len_slider.setRange(8, 64)
        self.len_slider.setValue(16)
        self.len_slider.valueChanged.connect(self._refresh_preview)
        len_row.addWidget(self.len_slider)
        self.len_label = QLabel("16")
        self.len_label.setFixedWidth(24)
        self.len_slider.valueChanged.connect(lambda v: self.len_label.setText(str(v)))
        len_row.addWidget(self.len_label)
        fl.addLayout(len_row)

        # Checkboxes
        chk_row = QHBoxLayout()
        self.chk_upper = QCheckBox("A-Z")
        self.chk_upper.setChecked(True)
        self.chk_lower = QCheckBox("a-z")
        self.chk_lower.setChecked(True)
        self.chk_digits = QCheckBox("0-9")
        self.chk_digits.setChecked(True)
        self.chk_symbols = QCheckBox("!@#")
        self.chk_symbols.setChecked(True)
        for chk in [self.chk_upper, self.chk_lower, self.chk_digits, self.chk_symbols]:
            chk.stateChanged.connect(self._refresh_preview)
            chk_row.addWidget(chk)
        fl.addLayout(chk_row)

        # Preview
        prev_row = QHBoxLayout()
        self.preview_field = QLineEdit()
        self.preview_field.setObjectName("mono")
        self.preview_field.setReadOnly(True)
        prev_row.addWidget(self.preview_field)

        use_btn = QPushButton("Use")
        use_btn.setObjectName("primary")
        use_btn.setMinimumWidth(60)
        use_btn.clicked.connect(self._use_preview)
        prev_row.addWidget(use_btn)

        refresh_btn = QPushButton("↺")
        refresh_btn.setObjectName("icon_btn")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self._refresh_preview)
        prev_row.addWidget(refresh_btn)
        fl.addLayout(prev_row)

        self._refresh_preview()
        return frame

    def _refresh_preview(self):
        pwd = generate_password(
            length=self.len_slider.value(),
            use_upper=self.chk_upper.isChecked(),
            use_lower=self.chk_lower.isChecked(),
            use_digits=self.chk_digits.isChecked(),
            use_symbols=self.chk_symbols.isChecked(),
        )
        self.preview_field.setText(pwd)

    def _use_preview(self):
        self.pw_input.setText(self.preview_field.text())
        self.gen_frame.setVisible(False)

    def _open_generator(self):
        visible = not self.gen_frame.isVisible()
        self.gen_frame.setVisible(visible)
        if visible:
            self._refresh_preview()
        self.adjustSize()

    def _toggle_visibility(self, checked: bool):
        self.pw_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.toggle_btn.setText("🔒" if checked else "👁")

    def _update_strength(self, text: str):
        if not text:
            self.strength_bar.setValue(0)
            self.strength_bar.setStyleSheet("")
            self.strength_label.setText("—")
            return
        label, score = password_strength(text)
        self.strength_bar.setValue(score)
        if label == "Weak":
            color = "#ef4444"
        elif label == "Medium":
            color = "#f59e0b"
        else:
            color = "#22c55e"
        self.strength_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}")
        self.strength_label.setText(label)
        self.strength_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

    def _populate(self, record):
        from core.encryption import decrypt
        self.title_input.setText(record["title"])
        self.username_input.setText(record["username"])
        try:
            plain = decrypt(record["encrypted_password"], self.encryption_key)
            self.pw_input.setText(plain)
        except Exception:
            self.pw_input.setText("")
        idx = self.category_combo.findText(record["category"])
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

    def _save(self):
        from core.encryption import encrypt
        title = self.title_input.text().strip()
        username = self.username_input.text().strip()
        password = self.pw_input.text()
        category = self.category_combo.currentText()

        if not title:
            QMessageBox.warning(self, "Validation", "Title is required.")
            return
        if not username:
            QMessageBox.warning(self, "Validation", "Username is required.")
            return
        if not password:
            QMessageBox.warning(self, "Validation", "Password is required.")
            return

        encrypted = encrypt(password, self.encryption_key)
        self.result_data = {
            "title": title,
            "username": username,
            "encrypted_password": encrypted,
            "category": category,
        }
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)
