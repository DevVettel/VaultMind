# VaultMind — Desktop Password Manager

A secure, offline desktop password manager built with Python, PyQt5, and SQLite.

## Screenshots

> _Add screenshots here after first run._

## Features

- **Master Password Protection** — All data encrypted with a key derived from your master password via PBKDF2HMAC (480,000 iterations). The master password is never stored.
- **Fernet Encryption** — Every stored password is AES-128-CBC encrypted at rest.
- **Password Generator** — Configurable length (8–64), charset options, live preview.
- **Strength Indicator** — Color-coded Weak / Medium / Strong meter on every password field.
- **Category Filtering** — Sidebar lets you filter by General, Email, Social, Banking, etc.
- **Clipboard Auto-clear** — Copied passwords are wiped from the clipboard after 30 seconds.
- **Auto-lock** — Vault locks automatically after 5 minutes of inactivity.
- **Dark UI** — Clean dark theme with a purple accent.

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/vaultmind.git
cd vaultmind

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python password_manager/main.py
```

**Requirements:** Python 3.10+

## Security Approach

| Concern | Implementation |
|---|---|
| Master password storage | SHA-256 hash of `salt + password` — raw password never written to disk |
| Key derivation | PBKDF2HMAC-SHA256, 480,000 iterations, 16-byte random salt |
| Password encryption | `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256) |
| Database file | `vaultmind.db` excluded from version control via `.gitignore` |
| Clipboard | Auto-cleared 30 seconds after copy via `threading.Timer` |
| Inactivity | App exits/locks after 5 minutes of no interaction |

## Project Structure

```
password_manager/
├── main.py                        # Entry point
├── core/
│   ├── encryption.py              # Key derivation, Fernet encrypt/decrypt
│   ├── database.py                # SQLite CRUD operations
│   └── password_generator.py     # Random password generation + strength scoring
├── ui/
│   ├── main_window.py             # QMainWindow with table, sidebar, toolbar
│   ├── add_password_dialog.py     # Add/Edit dialog with inline generator
│   └── master_password_dialog.py # First-launch setup + unlock screen
└── assets/icons/                  # (reserved for future icons)
```
