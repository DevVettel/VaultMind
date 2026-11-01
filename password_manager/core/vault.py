"""Master password setup and unlock, independent of the UI."""
from typing import Optional

from core import database, encryption


def is_first_launch() -> bool:
    return database.is_first_launch()


def create_vault(master_password: str) -> bytes:
    salt = encryption.generate_salt()
    key = encryption.derive_key(master_password, salt)
    database.store_master_credentials(salt, encryption.make_verifier(key))
    return key


def unlock_vault(master_password: str) -> Optional[bytes]:
    """Return the vault key if the password is correct, else None.

    Vaults created before the verifier existed are upgraded on the first
    successful unlock and their legacy hash is removed.
    """
    salt, verifier, legacy_hash = database.get_master_credentials()
    key = encryption.derive_key(master_password, salt)

    if verifier is not None:
        return key if encryption.check_verifier(key, verifier) else None

    if legacy_hash is not None and encryption.legacy_verify_password(
        master_password, salt, legacy_hash
    ):
        database.store_master_credentials(salt, encryption.make_verifier(key))
        return key

    return None
