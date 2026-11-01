# Contributing to VaultMind

Thanks for your interest in improving VaultMind!

## Getting Started

```bash
git clone https://github.com/DevVettel/VaultMind.git
cd VaultMind
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
python password_manager/main.py
```

To try things without touching your real vault, point the app at a throwaway database:

```bash
VAULTMIND_DB_PATH=/tmp/test.db python password_manager/main.py
```

## Before Opening a Pull Request

- `python -m pytest` passes (UI tests run headless; no window opens).
- `ruff check .` is clean.
- New logic in `core/` comes with tests in `tests/`.
- User-visible changes are noted under **Unreleased** in `CHANGELOG.md`.

## Project Rules

- Encryption happens only in `core/encryption.py`; database access only in `core/database.py`.
- Never log, print or persist the master password, the derived key or decrypted passwords.
- Never commit a `.db` file or a `.vmbackup` file.
- Security issues go through private reporting — see [SECURITY.md](SECURITY.md).

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add encrypted backup export
fix: stop icon buttons from being clipped in the table
docs: describe the threat model
test: cover legacy vault upgrade
chore: bump cryptography
```

## Branches

Work on a feature branch (`feat/...`, `fix/...`) and open a pull request against `main`.
