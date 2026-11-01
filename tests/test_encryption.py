import pytest
from cryptography.fernet import InvalidToken

from core import encryption


def test_roundtrip():
    key = encryption.derive_key("correct horse", encryption.generate_salt())
    token = encryption.encrypt("s3cret", key)
    assert token != "s3cret"
    assert encryption.decrypt(token, key) == "s3cret"


def test_wrong_key_cannot_decrypt():
    salt = encryption.generate_salt()
    token = encryption.encrypt("s3cret", encryption.derive_key("right", salt))
    with pytest.raises(InvalidToken):
        encryption.decrypt(token, encryption.derive_key("wrong", salt))


def test_derive_key_is_deterministic_per_salt():
    salt = encryption.generate_salt()
    assert encryption.derive_key("pw", salt) == encryption.derive_key("pw", salt)
    assert encryption.derive_key("pw", salt) != encryption.derive_key("pw", encryption.generate_salt())


def test_verifier():
    salt = encryption.generate_salt()
    key = encryption.derive_key("right", salt)
    token = encryption.make_verifier(key)
    assert encryption.check_verifier(key, token)
    assert not encryption.check_verifier(encryption.derive_key("wrong", salt), token)
    assert not encryption.check_verifier(key, "garbage")
