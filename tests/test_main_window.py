"""Headless checks of the auto-lock and clipboard behaviour."""
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QDialog

import ui.main_window as mw
from core import database, encryption, vault


class FakeClipboard:
    def __init__(self):
        self.value = ""

    def copy(self, v):
        self.value = v

    def paste(self):
        return self.value


def _window(db, qapp, monkeypatch):
    clip = FakeClipboard()
    monkeypatch.setattr(mw, "pyperclip", clip)
    key = vault.create_vault("master-password")
    rid = database.add_password("Mail", "me", encryption.encrypt("p@ss", key), "Email")
    win = mw.MainWindow(key)
    win.show()
    return win, clip, rid


def _select(win, rid):
    win.table.selectRow(win._row_ids.index(rid))


def test_activity_in_child_widget_resets_timer(db, qapp, monkeypatch):
    win, _, _ = _window(db, qapp, monkeypatch)
    try:
        win._inactivity_timer.stop()
        QApplication.sendEvent(win.search_box, QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a"))
        assert win._inactivity_timer.isActive()
    finally:
        win.close()


def test_copy_then_lock_clears_clipboard_and_relocks(db, qapp, monkeypatch):
    win, clip, rid = _window(db, qapp, monkeypatch)
    try:
        _select(win, rid)
        win._copy_password()
        assert clip.value == "p@ss"
        assert win._clipboard_timer.isActive()

        prompts = []
        monkeypatch.setattr(win, "_prompt_unlock", lambda: prompts.append(True))
        monkeypatch.setattr(mw.QTimer, "singleShot", lambda _ms, fn: fn())
        win._lock_vault()

        assert clip.value == ""
        assert win.enc_key is None
        assert win._locked and not win.isVisible()
        assert not win._inactivity_timer.isActive()
        assert prompts == [True]

        # Input while locked must not restart the lock timer.
        win._reset_inactivity()
        assert not win._inactivity_timer.isActive()
    finally:
        QApplication.instance().setQuitOnLastWindowClosed(True)
        win.close()


def test_unlock_restores_window(db, qapp, monkeypatch):
    win, _, _ = _window(db, qapp, monkeypatch)
    key = win.enc_key
    try:
        class AcceptingDialog:
            Accepted = QDialog.Accepted

            def __init__(self, unlock, **_kw):
                self.enc_key = unlock("master-password")

            def exec_(self):
                return QDialog.Accepted

        monkeypatch.setattr(mw, "MasterPasswordDialog", AcceptingDialog)
        win._locked = True
        win.enc_key = None
        win.hide()
        win._prompt_unlock()

        assert win.enc_key == key
        assert not win._locked and win.isVisible()
        assert win._inactivity_timer.isActive()
    finally:
        win.close()


def test_clipboard_left_alone_if_user_copied_something_else(db, qapp, monkeypatch):
    win, clip, rid = _window(db, qapp, monkeypatch)
    try:
        _select(win, rid)
        win._copy_password()
        clip.value = "something the user copied later"
        win._clear_clipboard_now()
        assert clip.value == "something the user copied later"
    finally:
        win.close()


def test_export_then_import_from_ui(db, qapp, monkeypatch, tmp_path):
    win, _, rid = _window(db, qapp, monkeypatch)
    out = str(tmp_path / "b.vmbackup")
    infos = []
    try:
        monkeypatch.setattr(mw.QFileDialog, "getSaveFileName", lambda *a, **k: (out, ""))
        monkeypatch.setattr(mw.QFileDialog, "getOpenFileName", lambda *a, **k: (out, ""))
        monkeypatch.setattr(mw.QInputDialog, "getText", lambda *a, **k: ("backup-pw", True))
        monkeypatch.setattr(mw.QMessageBox, "information", lambda _p, title, _m: infos.append(title))
        monkeypatch.setattr(mw.QMessageBox, "warning", lambda _p, title, m: infos.append(f"WARN {m}"))

        win._export_backup()
        database.delete_password(rid)
        win._import_backup()

        assert infos == ["Export Complete", "Import Complete"]
        assert [r["title"] for r in database.get_all_passwords()] == ["Mail"]
        assert win.table.rowCount() == 1
    finally:
        win.close()


def test_icon_buttons_fit_their_cells(db, qapp, monkeypatch):
    from PyQt5.QtWidgets import QPushButton
    database.add_password("Site", "u", "c", "Web", url="https://example.com")
    win, _, _ = _window(db, qapp, monkeypatch)
    try:
        win.resize(1280, 760)
        qapp.processEvents()
        for row in range(win.table.rowCount()):
            for col in (0, 5):
                cell = win.table.cellWidget(row, col)
                if cell is None:
                    continue
                btn = cell.findChild(QPushButton)
                assert cell.width() >= btn.width(), f"row {row} col {col} clipped"
    finally:
        win.close()
