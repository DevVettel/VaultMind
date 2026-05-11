<h1 align="center">
  <img src="docs/icon-0.png" width="48" height="48" alt="VaultMind icon"/><br/>
  VaultMind
</h1>

<p align="center">
  A secure, fully offline password manager for Windows — built with Python and PyQt5.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/PyQt5-5.15%2B-41cd52?style=flat-square"/>
  <img src="https://img.shields.io/badge/Encryption-AES--256-072182?style=flat-square"/>
  <img src="https://img.shields.io/badge/Storage-Local%20only-lightgrey?style=flat-square"/>
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?style=flat-square&logo=windows"/>
</p>

---

## Overview

VaultMind stores and encrypts all your credentials locally on your machine. No cloud, no sync, no accounts — your data never leaves your device. Every password is encrypted with a key derived from your master password, which is never stored anywhere.

---

## Features

| | |
|---|---|
| **Master Password Vault** | Key derived via PBKDF2HMAC-SHA256 (480,000 iterations). Master password is never stored. |
| **AES-256 Encryption** | Every credential is encrypted at rest using `cryptography.Fernet` (AES-128-CBC + HMAC-SHA256). |
| **Password Generator** | Configurable length (8–64 chars), uppercase, lowercase, digits, and symbols with live preview. |
| **Strength Meter** | Real-time color-coded Weak / Medium / Strong indicator on every password field. |
| **Category Filtering** | Sidebar filters by General, Email, Social, Banking, Work, Shopping, and more. |
| **Clipboard Auto-clear** | Copied passwords are automatically wiped from the clipboard after 30 seconds. |
| **Auto-lock** | Vault locks and exits after 5 minutes of inactivity. |
| **Dark Theme** | Clean dark UI with native Windows title bar integration. |

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/DevVettel/VaultMind.git
cd VaultMind

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python password_manager/main.py
```

**Requirements:** Python 3.10+, Windows 10/11

---

## Security

| Concern | Implementation |
|---|---|
| Master password | Verified via PBKDF2HMAC hash — raw password never written to disk |
| Key derivation | PBKDF2HMAC-SHA256, 480,000 iterations, 16-byte random salt |
| Credential encryption | `cryptography.Fernet` — AES-128-CBC + HMAC-SHA256 integrity check |
| Database | `vaultmind.db` is local-only and excluded from version control |
| Clipboard | Auto-cleared 30 seconds after copy via background thread |
| Inactivity | Application locks after 5 minutes of no user interaction |

---

## Project Structure

```
VaultMind/
├── password_manager/
│   ├── main.py                         # Entry point
│   ├── core/
│   │   ├── database.py                 # SQLite CRUD operations
│   │   ├── encryption.py               # Key derivation & Fernet encrypt/decrypt
│   │   └── password_generator.py       # Password generation & strength scoring
│   └── ui/
│       ├── main_window.py              # Main window — table, sidebar, toolbar
│       ├── add_password_dialog.py      # Add / Edit dialog with inline generator
│       ├── master_password_dialog.py   # First-launch setup & unlock screen
│       └── utils.py                    # Windows dark title bar helper
├── docs/
│   ├── icon-0.png                      # App icon 48×48
│   └── icon-1.png                      # App icon 32×32
├── requirements.txt
└── .gitignore
```

---

## Dependencies

```
PyQt5 >= 5.15
cryptography >= 41.0
pyperclip >= 1.8
```

---

## License

This project is licensed under the [MIT License](LICENSE).
