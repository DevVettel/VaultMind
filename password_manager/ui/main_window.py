import threading
import webbrowser
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QToolBar, QAction, QStatusBar, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QAbstractItemView, QFrame, QApplication,
    QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

import pyperclip

from core import database, encryption
from ui.add_password_dialog import AddPasswordDialog
from ui.utils import apply_dark_titlebar


STYLE = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget#central {
    background-color: #1e1e2e;
}
QSplitter::handle {
    background-color: #2a2a3e;
    width: 1px;
}
QListWidget {
    background-color: #181825;
    color: #e2e8f0;
    border: none;
    font-size: 15px;
    padding: 8px 0;
    outline: none;
}
QListWidget::item {
    padding: 10px 18px;
    border-radius: 4px;
    margin: 1px 6px;
}
QListWidget::item:selected {
    background-color: #072182;
    color: white;
}
QListWidget::item:hover:!selected {
    background-color: #2a2a3e;
}
QTableWidget {
    background-color: #1e1e2e;
    color: #e2e8f0;
    border: none;
    gridline-color: #2a2a3e;
    font-size: 14px;
    outline: none;
    selection-background-color: #0d2d6b;
}
QTableWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid #2a2a3e;
}
QTableWidget::item:selected {
    background-color: #0d2d6b;
    color: #e2e8f0;
}
QHeaderView::section {
    background-color: #181825;
    color: #94a3b8;
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid #3d3d5c;
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #2a2a3e;
    spacing: 4px;
    padding: 6px 10px;
}
QToolBar::separator {
    background-color: #3d3d5c;
    width: 1px;
    margin: 4px 6px;
}
QToolButton {
    background-color: transparent;
    color: #e2e8f0;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-size: 14px;
}
QToolButton:hover {
    background-color: #2a2a3e;
}
QToolButton:pressed {
    background-color: #3d3d5c;
}
QLineEdit#search {
    background-color: #2a2a3e;
    color: #e2e8f0;
    border: 1px solid #3d3d5c;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 14px;
    min-width: 220px;
    max-width: 300px;
}
QLineEdit#search:focus {
    border-color: #072182;
}
QStatusBar {
    background-color: #181825;
    color: #94a3b8;
    font-size: 13px;
    border-top: 1px solid #2a2a3e;
}
QLabel#sidebar_header {
    color: #94a3b8;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 10px 18px 6px 18px;
}
QPushButton#fav_btn {
    background-color: transparent;
    border: none;
    font-size: 18px;
    padding: 2px 4px;
}
QPushButton#url_btn {
    background-color: transparent;
    border: none;
    font-size: 15px;
    color: #5b8dee;
    padding: 2px 4px;
}
QPushButton#url_btn:hover {
    color: #7ba7f5;
}
"""


def _cell_widget(btn: QPushButton) -> QWidget:
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    layout = QHBoxLayout(container)
    layout.setAlignment(Qt.AlignCenter)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(btn)
    return container


class _Signals(QObject):
    lock_vault = pyqtSignal()


class MainWindow(QMainWindow):
    def __init__(self, enc_key: bytes):
        super().__init__()
        self.enc_key = enc_key
        self.current_category = "All"
        self.current_search = ""
        self._clipboard_timer = None
        self._toast = None
        self._signals = _Signals()
        self._signals.lock_vault.connect(self._lock_vault)
        self._build_ui()
        self._setup_inactivity_timer()
        self.setStyleSheet(STYLE)
        self._refresh_table()
        self._refresh_sidebar()

    def _build_ui(self):
        self.setWindowTitle("VaultMind — Password Manager")
        self.setMinimumSize(1000, 680)
        self.resize(1280, 820)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._build_toolbar()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Sidebar
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #181825;")
        sidebar.setFixedWidth(230)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.category_list = QListWidget()
        self.category_list.currentItemChanged.connect(self._on_category_changed)
        sidebar_layout.addWidget(self.category_list)
        splitter.addWidget(sidebar)

        # Table area
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Title", "Username", "Category", "Updated", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 44)
        self.table.setColumnWidth(5, 44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.doubleClicked.connect(self._edit_selected)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_container)

        splitter.setSizes([230, 1050])
        root_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        self.status_bar.addWidget(self.status_label)
        self._selection_label = QLabel()
        self._selection_label.setStyleSheet("color: #5b8dee; font-size: 13px; padding-left: 6px; background: transparent;")
        self.status_bar.addWidget(self._selection_label)
        self.lock_status = QLabel("  🔒 Vault Open")
        self.lock_status.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent; padding-right: 8px;")
        self.status_bar.addPermanentWidget(self.lock_status)

    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setFloatable(False)
        self.addToolBar(tb)

        add_action = QAction("＋ Add", self)
        add_action.triggered.connect(self._add_password)
        tb.addAction(add_action)

        edit_action = QAction("✎ Edit", self)
        edit_action.triggered.connect(self._edit_selected)
        tb.addAction(edit_action)

        del_action = QAction("✕ Delete", self)
        del_action.triggered.connect(self._delete_selected)
        tb.addAction(del_action)

        tb.addSeparator()

        copy_action = QAction("⎘ Copy Password", self)
        copy_action.triggered.connect(self._copy_password)
        tb.addAction(copy_action)

        tb.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        search_label = QLabel("  Search: ")
        search_label.setStyleSheet("color: #94a3b8; font-size: 12px; background: transparent;")
        tb.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("search")
        self.search_box.setPlaceholderText("Search passwords...")
        self.search_box.textChanged.connect(self._on_search)
        tb.addWidget(self.search_box)

    def _setup_inactivity_timer(self):
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setInterval(5 * 60 * 1000)
        self._inactivity_timer.timeout.connect(self._lock_vault)
        self._inactivity_timer.start()

    def _reset_inactivity(self):
        self._inactivity_timer.start()

    def mousePressEvent(self, event):
        self._reset_inactivity()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        self._reset_inactivity()
        super().keyPressEvent(event)

    def _lock_vault(self):
        self._inactivity_timer.stop()
        QMessageBox.information(
            self, "Vault Locked",
            "Your vault has been locked due to inactivity.\nPlease restart to unlock."
        )
        QApplication.quit()

    def _refresh_sidebar(self):
        self.category_list.blockSignals(True)
        self.category_list.clear()

        header_font = QFont()
        header_font.setPointSize(9)
        header_font.setBold(True)

        def add_section_header(text):
            item = QListWidgetItem(f"  {text}")
            item.setFlags(Qt.NoItemFlags)
            item.setFont(header_font)
            item.setForeground(QColor("#64748b"))
            self.category_list.addItem(item)

        add_section_header("SMART VIEWS")
        for key, display in [("All", "All"), ("Favorites", "★  Favorites"), ("Recent", "⏱  Recent")]:
            item = QListWidgetItem(f"   {display}")
            item.setData(Qt.UserRole, key)
            self.category_list.addItem(item)
            if key == self.current_category:
                self.category_list.setCurrentItem(item)

        sep = QListWidgetItem()
        sep.setFlags(Qt.NoItemFlags)
        sep.setBackground(QColor("#2a2a3e"))
        self.category_list.addItem(sep)

        add_section_header("CATEGORIES")
        for cat in database.get_categories():
            item = QListWidgetItem(f"   {cat}")
            item.setData(Qt.UserRole, cat)
            self.category_list.addItem(item)
            if cat == self.current_category:
                self.category_list.setCurrentItem(item)

        if self.category_list.currentItem() is None:
            self.category_list.setCurrentRow(1)

        self.category_list.blockSignals(False)

    def _on_category_changed(self, current, _previous):
        if current:
            name = current.data(Qt.UserRole)
            if name is not None:
                self.current_category = name
                self.current_search = ""
                self.search_box.blockSignals(True)
                self.search_box.clear()
                self.search_box.blockSignals(False)
                self._refresh_table()

    def _on_search(self, text: str):
        self._reset_inactivity()
        self.current_search = text
        self._refresh_table()

    def _refresh_table(self):
        if self.current_search:
            rows = database.search_passwords(self.current_search)
        else:
            rows = database.get_all_passwords(self.current_category)

        self.table.setRowCount(len(rows))
        self._row_ids = []

        for i, row in enumerate(rows):
            rid = row["id"]
            self._row_ids.append(rid)

            # Col 0: favorite toggle button
            is_fav = bool(row["is_favorite"])
            fav_btn = QPushButton("★" if is_fav else "☆")
            fav_btn.setObjectName("fav_btn")
            fav_btn.setFixedSize(32, 32)
            fav_btn.setStyleSheet(
                f"color: {'#f59e0b' if is_fav else '#4a5568'};"
                "background: transparent; border: none; font-size: 18px;"
            )
            fav_btn.clicked.connect(lambda _checked, r=rid: self._toggle_favorite(r))
            self.table.setCellWidget(i, 0, _cell_widget(fav_btn))

            # Cols 1-4: text data
            self.table.setItem(i, 1, QTableWidgetItem(row["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(row["username"]))
            self.table.setItem(i, 3, QTableWidgetItem(row["category"]))
            dt = row["updated_at"][:10] if row["updated_at"] else ""
            self.table.setItem(i, 4, QTableWidgetItem(dt))

            # Col 5: URL open button (only if URL is set)
            url = row["url"] or ""
            if url:
                url_btn = QPushButton("🔗")
                url_btn.setObjectName("url_btn")
                url_btn.setFixedSize(32, 32)
                url_btn.setToolTip(url)
                url_btn.clicked.connect(lambda _checked, u=url: webbrowser.open(u))
                self.table.setCellWidget(i, 5, _cell_widget(url_btn))
            else:
                self.table.removeCellWidget(i, 5)

        count = database.count_passwords()
        self.status_label.setText(f"  {count} password{'s' if count != 1 else ''} stored")
        self._selection_label.setText("")

    def _toggle_favorite(self, record_id: int):
        database.toggle_favorite(record_id)
        self._refresh_table()

    def _selected_row_id(self):
        rows = self.table.selectedItems()
        if not rows:
            return None
        row_idx = self.table.currentRow()
        if row_idx < 0 or row_idx >= len(self._row_ids):
            return None
        return self._row_ids[row_idx]

    def _on_selection_changed(self):
        row_idx = self.table.currentRow()
        if row_idx >= 0 and self.table.item(row_idx, 1):
            title = self.table.item(row_idx, 1).text()
            self._selection_label.setText(f"  ·  {title} selected")
        else:
            self._selection_label.setText("")

    def _show_copy_toast(self):
        if self._toast:
            try:
                self._toast.deleteLater()
            except Exception:
                pass
            self._toast = None

        toast = QLabel("  ✓  Password copied to clipboard  ", self)
        toast.setAlignment(Qt.AlignCenter)
        toast.setStyleSheet("""
            background-color: #0d2d6b;
            color: #ffffff;
            border: 1px solid #3a5fc8;
            border-radius: 10px;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 22px;
        """)
        toast.adjustSize()
        toast.setFixedHeight(46)

        x = (self.width() - toast.width()) // 2
        y = self.height() - 110
        toast.move(x, y)
        toast.show()
        toast.raise_()
        self._toast = toast

        QTimer.singleShot(2500, lambda: self._dismiss_toast(toast))

    def _dismiss_toast(self, toast):
        try:
            toast.deleteLater()
        except Exception:
            pass
        if self._toast is toast:
            self._toast = None

    def _add_password(self):
        self._reset_inactivity()
        dlg = AddPasswordDialog(self.enc_key, parent=self)
        if dlg.exec_() == dlg.Accepted and dlg.result_data:
            d = dlg.result_data
            database.add_password(
                d["title"], d["username"], d["encrypted_password"], d["category"],
                d.get("url", ""), d.get("notes", "")
            )
            self._refresh_sidebar()
            self._refresh_table()

    def _edit_selected(self):
        self._reset_inactivity()
        rec_id = self._selected_row_id()
        if rec_id is None:
            QMessageBox.information(self, "No Selection", "Please select a password to edit.")
            return

        rows = database.get_all_passwords()
        record = next((r for r in rows if r["id"] == rec_id), None)
        if record is None:
            return

        dlg = AddPasswordDialog(self.enc_key, record=record, parent=self)
        if dlg.exec_() == dlg.Accepted and dlg.result_data:
            d = dlg.result_data
            database.update_password(
                rec_id, d["title"], d["username"], d["encrypted_password"], d["category"],
                d.get("url", ""), d.get("notes", "")
            )
            self._refresh_sidebar()
            self._refresh_table()

    def _delete_selected(self):
        self._reset_inactivity()
        rec_id = self._selected_row_id()
        if rec_id is None:
            QMessageBox.information(self, "No Selection", "Please select a password to delete.")
            return

        title = self.table.item(self.table.currentRow(), 1).text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete password for '{title}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            database.delete_password(rec_id)
            self._refresh_sidebar()
            self._refresh_table()

    def _copy_password(self):
        self._reset_inactivity()
        rec_id = self._selected_row_id()
        if rec_id is None:
            QMessageBox.information(self, "No Selection", "Please select a password to copy.")
            return

        rows = database.get_all_passwords()
        record = next((r for r in rows if r["id"] == rec_id), None)
        if record is None:
            return

        try:
            plain = encryption.decrypt(record["encrypted_password"], self.enc_key)
            pyperclip.copy(plain)
            database.update_last_used(rec_id)
            self._show_copy_toast()

            if self._clipboard_timer:
                self._clipboard_timer.cancel()

            def clear_clipboard():
                try:
                    if pyperclip.paste() == plain:
                        pyperclip.copy("")
                except Exception:
                    pass

            self._clipboard_timer = threading.Timer(30, clear_clipboard)
            self._clipboard_timer.daemon = True
            self._clipboard_timer.start()

            QTimer.singleShot(30500, lambda: self._refresh_table())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not decrypt password:\n{e}")

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)

    def closeEvent(self, event):
        if self._clipboard_timer:
            self._clipboard_timer.cancel()
        super().closeEvent(event)
