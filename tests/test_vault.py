import hashlib

from core import database, encryption, vault


def test_create_then_unlock(db):
    assert vault.is_first_launch()
    key = vault.create_vault("master-password")
    assert not vault.is_first_launch()
    assert vault.unlock_vault("master-password") == key
    assert vault.unlock_vault("wrong-password") is None


def test_no_password_hash_is_stored(db):
    vault.create_vault("master-password")
    salt, verifier, legacy_hash = database.get_master_credentials()
    assert len(salt) == 16
    assert verifier is not None
    assert legacy_hash is None


def _make_legacy_vault(password):
    """Recreate the meta rows an older VaultMind version wrote."""
    salt = encryption.generate_salt()
    legacy_hash = hashlib.sha256(salt + password.encode()).hexdigest()
    with database.get_connection() as conn:
        conn.execute("INSERT INTO meta VALUES ('salt', ?)", (salt.hex(),))
        conn.execute("INSERT INTO meta VALUES ('hash', ?)", (legacy_hash,))
    return salt


def test_legacy_vault_is_upgraded_on_unlock(db):
    salt = _make_legacy_vault("old-master")
    old_key = encryption.derive_key("old-master", salt)
    rec = database.add_password("Mail", "me", encryption.encrypt("p@ss", old_key), "Email")

    assert vault.unlock_vault("wrong") is None
    _, verifier, legacy_hash = database.get_master_credentials()
    assert verifier is None and legacy_hash is not None  # untouched by a failed attempt

    key = vault.unlock_vault("old-master")
    assert key == old_key
    _, verifier, legacy_hash = database.get_master_credentials()
    assert verifier is not None and legacy_hash is None

    # Existing entries still decrypt and the upgraded vault keeps working.
    assert encryption.decrypt(database.get_password(rec)["encrypted_password"], key) == "p@ss"
    assert vault.unlock_vault("old-master") == key
    assert vault.unlock_vault("wrong") is None
