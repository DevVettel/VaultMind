import string

import pytest

from core import password_generator as pg

SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"


@pytest.mark.parametrize("length", [8, 16, 64])
def test_length_and_all_classes_present(length):
    for _ in range(50):
        pwd = pg.generate_password(length)
        assert len(pwd) == length
        assert any(c in string.ascii_uppercase for c in pwd)
        assert any(c in string.ascii_lowercase for c in pwd)
        assert any(c in string.digits for c in pwd)
        assert any(c in SYMBOLS for c in pwd)


def test_respects_disabled_classes():
    pwd = pg.generate_password(32, use_upper=False, use_symbols=False)
    assert not any(c in string.ascii_uppercase or c in SYMBOLS for c in pwd)


def test_no_classes_falls_back_to_alphanumeric():
    pwd = pg.generate_password(20, False, False, False, False)
    assert len(pwd) == 20 and pwd.isalnum()


def test_uses_csprng():
    assert not hasattr(pg, "random")
    assert len({pg.generate_password(16) for _ in range(200)}) == 200


@pytest.mark.parametrize("pwd,label", [("abc", "Weak"), ("abcdefgh12", "Medium"), ("Abcdefgh12!@xyzQ", "Strong")])
def test_strength(pwd, label):
    assert pg.password_strength(pwd)[0] == label
