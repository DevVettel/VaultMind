from PyQt5.QtWidgets import QPushButton

from core import encryption
from ui.add_password_dialog import AddPasswordDialog


def _dialog(qapp):
    dlg = AddPasswordDialog(encryption.derive_key("pw", b"0" * 16))
    dlg.show()
    qapp.processEvents()
    return dlg


def _button(dlg, text):
    return next(b for b in dlg.findChildren(QPushButton) if b.text() == text)


def test_generate_opens_full_size_panel(qapp):
    dlg = _dialog(qapp)
    try:
        start_height = dlg.height()
        _button(dlg, "Generate").click()
        qapp.processEvents()

        assert dlg.gen_frame.isVisible()
        # The panel must get its real height, not be squeezed to a strip.
        assert dlg.gen_frame.height() >= dlg.gen_frame.minimumSizeHint().height()
        assert dlg.height() > start_height
        assert len(dlg.preview_field.text()) == 16
    finally:
        dlg.close()


def test_use_fills_password_and_closes_panel(qapp):
    dlg = _dialog(qapp)
    try:
        start_height = dlg.height()
        _button(dlg, "Generate").click()
        qapp.processEvents()
        generated = dlg.preview_field.text()

        _button(dlg, "Use").click()
        qapp.processEvents()

        assert dlg.pw_input.text() == generated
        assert not dlg.gen_frame.isVisible()
        assert dlg.height() == start_height
    finally:
        dlg.close()
