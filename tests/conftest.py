import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "password_manager"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core import database  # noqa: E402


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Point the app at a fresh, throwaway SQLite file."""
    path = tmp_path / "vault.db"
    monkeypatch.setenv("VAULTMIND_DB_PATH", str(path))
    monkeypatch.setattr(database, "DB_PATH", None)
    database.initialize_db()
    return path


@pytest.fixture(scope="session")
def qapp():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app
