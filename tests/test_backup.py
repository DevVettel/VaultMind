import json

import pytest

from core import backup, database, encryption, vault

SECRET = "correct-horse-battery-staple-42"


def _seed(key):
    a = database.add_password("Mail", "me", encryption.encrypt(SECRET, key), "Email",
                              url="https://mail.example", notes="n")
    database.toggle_favorite(a)
    database.add_password("Bank", "acct", encryption.encrypt("p2", key), "Banking")


def test_roundtrip_into_another_vault(db, tmp_path, monkeypatch):
    key = vault.create_vault("master-one")
    _seed(key)
    out = tmp_path / "b.vmbackup"
    assert backup.export_backup(str(out), key, "backup-pw") == 2

    raw = out.read_text()
    assert SECRET not in raw and "mail.example" not in raw  # nothing readable in the file

    # Restore into a brand-new vault with a different master password.
    monkeypatch.setenv("VAULTMIND_DB_PATH", str(tmp_path / "other.db"))
    monkeypatch.setattr(database, "DB_PATH", None)
    database.initialize_db()
    key2 = vault.create_vault("master-two")

    assert backup.import_backup(str(out), key2, "backup-pw") == {"added": 2, "skipped": 0}
    rows = {r["title"]: r for r in database.get_all_passwords()}
    assert encryption.decrypt(rows["Mail"]["encrypted_password"], key2) == SECRET
    assert rows["Mail"]["is_favorite"] == 1 and rows["Mail"]["url"] == "https://mail.example"
    assert rows["Bank"]["category"] == "Banking"


def test_reimport_skips_duplicates(db, tmp_path):
    key = vault.create_vault("master")
    _seed(key)
    out = tmp_path / "b.vmbackup"
    backup.export_backup(str(out), key, "pw")
    assert backup.import_backup(str(out), key, "pw") == {"added": 0, "skipped": 2}
    assert database.count_passwords() == 2


def test_wrong_password(db, tmp_path):
    key = vault.create_vault("master")
    out = tmp_path / "b.vmbackup"
    backup.export_backup(str(out), key, "pw")
    with pytest.raises(backup.BackupError, match="Wrong backup password"):
        backup.read_backup(str(out), "nope")


@pytest.mark.parametrize("content", ["not json", json.dumps({"format": "other"}), json.dumps([1])])
def test_rejects_foreign_files(tmp_path, content):
    f = tmp_path / "x.json"
    f.write_text(content)
    with pytest.raises(backup.BackupError):
        backup.read_backup(str(f), "pw")
