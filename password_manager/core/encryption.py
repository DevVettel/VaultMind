import os
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def generate_salt() -> bytes:
    return os.urandom(16)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def hash_password(password: str, salt: bytes) -> str:
    return hashlib.sha256(salt + password.encode()).hexdigest()


def verify_password(password: str, salt: bytes, stored_hash: str) -> bool:
    return hash_password(password, salt) == stored_hash


def encrypt(plaintext: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(ciphertext.encode()).decode()
