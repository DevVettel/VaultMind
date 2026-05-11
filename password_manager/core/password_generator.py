import random
import string


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    charset = ""
    guaranteed = []

    if use_upper:
        charset += string.ascii_uppercase
        guaranteed.append(random.choice(string.ascii_uppercase))
    if use_lower:
        charset += string.ascii_lowercase
        guaranteed.append(random.choice(string.ascii_lowercase))
    if use_digits:
        charset += string.digits
        guaranteed.append(random.choice(string.digits))
    if use_symbols:
        symbols = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        charset += symbols
        guaranteed.append(random.choice(symbols))

    if not charset:
        charset = string.ascii_letters + string.digits
        guaranteed = []

    remaining = length - len(guaranteed)
    if remaining < 0:
        remaining = 0

    pwd_chars = guaranteed + [random.choice(charset) for _ in range(remaining)]
    random.shuffle(pwd_chars)
    return "".join(pwd_chars[:length])


def password_strength(password: str) -> tuple[str, int]:
    """Return (label, score 0-100)."""
    score = 0
    length = len(password)

    if length >= 8:
        score += 20
    if length >= 12:
        score += 15
    if length >= 16:
        score += 15

    if any(c.isupper() for c in password):
        score += 10
    if any(c.islower() for c in password):
        score += 10
    if any(c.isdigit() for c in password):
        score += 10
    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        score += 20

    score = min(score, 100)

    if score < 40:
        return "Weak", score
    elif score < 70:
        return "Medium", score
    else:
        return "Strong", score
