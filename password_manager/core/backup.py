"""Encrypted export / import of the whole vault.

A backup is a small JSON envelope around a single Fernet token. The token is
encrypted with a key derived from a backup password using its own random
salt, so a backup file is independent of the vault it came from and can be
restored into any vault.
"""
import json
from typing import Dict, List

from cryptography.fernet import InvalidToken

from core import database, encryption

FORMAT = "vaultmind-backup"
FORMAT_VERSION = 1
_FIELDS = ("title", "username", "category", "url", "notes", "is_favorite")


class BackupError(Exception):
    """Raised for unreadable files, wrong passwords and unsupported formats."""


def export_backup(path: str, vault_key: bytes, backup_password: str) -> int:
    """Write every entry to `path`, encrypted with `backup_password`.

    Returns the number of exported entries.
    """
    entries: List[Dict] = []
    for row in database.get_all_passwords():
        entry = {f: row[f] for f in _FIELDS}
        entry["password"] = encryption.decrypt(row["encrypted_password"], vault_key)
        entries.append(entry)

    salt = encryption.generate_salt()
    key = encryption.derive_key(backup_password, salt)
    envelope = {
        "format": FORMAT,
        "version": FORMAT_VERSION,
        "kdf": "pbkdf2-sha256",
        "iterations": encryption.KDF_ITERATIONS,
        "salt": salt.hex(),
        "data": encryption.encrypt(json.dumps({"entries": entries}), key),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(envelope, fh, indent=2)
    return len(entries)


def read_backup(path: str, backup_password: str) -> List[Dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            envelope = json.load(fh)
    except (OSError, ValueError) as e:
        raise BackupError(f"Could not read backup file: {e}") from e

    if not isinstance(envelope, dict) or envelope.get("format") != FORMAT:
        raise BackupError("This is not a VaultMind backup file.")
    if envelope.get("version") != FORMAT_VERSION:
        raise BackupError(f"Unsupported backup version: {envelope.get('version')}")
    if envelope.get("iterations") != encryption.KDF_ITERATIONS:
        raise BackupError("Unsupported key derivation settings.")

    try:
        key = encryption.derive_key(backup_password, bytes.fromhex(envelope["salt"]))
        payload = json.loads(encryption.decrypt(envelope["data"], key))
    except InvalidToken:
        raise BackupError("Wrong backup password.") from None
    except (KeyError, TypeError, ValueError) as e:
        raise BackupError(f"Backup file is corrupted: {e}") from e

    return payload.get("entries", [])


def import_backup(path: str, vault_key: bytes, backup_password: str) -> Dict[str, int]:
    """Add entries from a backup into the current vault.

    Entries already present (same title, username and password) are skipped,
    so importing the same file twice is harmless.
    """
    entries = read_backup(path, backup_password)

    existing = set()
    for row in database.get_all_passwords():
        existing.add((row["title"], row["username"],
                      encryption.decrypt(row["encrypted_password"], vault_key)))

    added = skipped = 0
    for e in entries:
        ident = (e["title"], e.get("username", ""), e["password"])
        if ident in existing:
            skipped += 1
            continue
        rid = database.add_password(
            e["title"], e.get("username", ""),
            encryption.encrypt(e["password"], vault_key),
            e.get("category") or "General",
            e.get("url") or "", e.get("notes") or "",
        )
        if e.get("is_favorite"):
            database.toggle_favorite(rid)
        existing.add(ident)
        added += 1
    return {"added": added, "skipped": skipped}
