import base64
import hashlib
import hmac
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KDF_ITERATIONS = 480_000
VERIFIER_PLAINTEXT = "vaultmind-verifier-v1"


def generate_salt() -> bytes:
    return os.urandom(16)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def make_verifier(key: bytes) -> str:
    """Encrypt a known constant with the vault key.

    Checking the master password then costs a full PBKDF2 derivation per
    guess, unlike a plain hash.
    """
    return Fernet(key).encrypt(VERIFIER_PLAINTEXT.encode()).decode()


def check_verifier(key: bytes, token: str) -> bool:
    try:
        return Fernet(key).decrypt(token.encode()).decode() == VERIFIER_PLAINTEXT
    except InvalidToken:
        return False


def legacy_verify_password(password: str, salt: bytes, stored_hash: str) -> bool:
    """Check against the old single-round SHA256 hash (pre-verifier vaults)."""
    candidate = hashlib.sha256(salt + password.encode()).hexdigest()
    return hmac.compare_digest(candidate, stored_hash)


def encrypt(plaintext: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(ciphertext.encode()).decode()
