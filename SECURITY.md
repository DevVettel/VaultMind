# Security Policy

VaultMind stores secrets, so security reports are taken seriously.

## Reporting a Vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's private reporting instead: **Security → Report a vulnerability** on this repository. Include steps to reproduce, the affected version and your OS. You should get a first response within 7 days. Once a fix is released, you will be credited unless you prefer otherwise.

## Supported Versions

Only the latest release receives security fixes.

## Threat Model

### What VaultMind protects against

- **Theft of the vault file** (lost laptop, stolen backup, synced folder leak). Every entry is encrypted with Fernet (AES-128-CBC + HMAC-SHA256) using a key derived from the master password via PBKDF2-HMAC-SHA256 with 480,000 iterations and a random 16-byte salt. The master password and the key are never written to disk. Each guess at the master password costs a full key derivation.
- **Tampering with stored entries.** Fernet's HMAC rejects modified ciphertext.
- **Shoulder-surfing and walk-away access.** The vault locks after 5 minutes without input and discards the key from memory; copied passwords are cleared from the clipboard after 30 seconds, on lock and on exit.
- **Leaking backups.** Exported `.vmbackup` files are encrypted with their own password and salt.

### What VaultMind does *not* protect against

- **A compromised computer.** Malware, keyloggers or anyone with control of your running user session can read what you type, the clipboard and process memory.
- **Weak master passwords.** Key stretching slows down guessing; it cannot save a password like `password123`.
- **Metadata.** Titles, usernames, categories, URLs and notes are stored unencrypted in the local SQLite file so they can be searched; only passwords are encrypted. Do not put secrets in the notes field.
- **Memory forensics.** Python cannot reliably wipe strings from memory; decrypted values may remain in RAM until overwritten.
- **Forgotten master passwords.** There is no recovery. Keep an encrypted backup.

## Storage Location

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/VaultMind/vaultmind.db` |
| Windows | `%APPDATA%\VaultMind\vaultmind.db` |
| Linux | `$XDG_DATA_HOME/VaultMind/vaultmind.db` (default `~/.local/share/...`) |
