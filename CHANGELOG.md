# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-11-01

### Security
- Master password is now verified by decrypting a known token with the PBKDF2-derived key instead of a single-round SHA256 hash, so every guess costs 480,000 iterations. Existing vaults are upgraded automatically on first unlock.
- Password generator uses the `secrets` CSPRNG instead of `random`.
- Clipboard is also cleared when the vault locks and when the app exits.

### Added
- Encrypted backup export / import (`.vmbackup`).
- macOS support (system fonts, per-platform data directory).
- Prebuilt macOS and Windows apps attached to GitHub releases.
- New shield app icon in every size, used for the window, the Dock / taskbar and the packaged apps.
- Test suite, CI on macOS / Windows / Linux, SECURITY.md and contribution guidelines.

### Changed
- Auto-lock now really locks: the window hides, the key is discarded and the master password is asked again, instead of quitting.
- Wrong master password no longer quits the app; you can try again.
- Minimum Python version is 3.9.
- Generator checkboxes show a tick and are easier to tell apart.

### Fixed
- Auto-lock could trigger while you were actively using the table or search box.
- Favourite and link buttons were clipped in the password table.
- Generate button appeared to do nothing: the generator panel was squeezed to an empty strip because the dialog did not grow. The Notes field was also cut off.

## [1.0.0] - 2026-05-11

### Added
- Initial release: master-password vault, Fernet encryption, password generator with strength meter, categories, favourites, recent items, clipboard auto-clear and auto-lock.

[Unreleased]: https://github.com/DevVettel/VaultMind/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/DevVettel/VaultMind/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/DevVettel/VaultMind/releases/tag/v1.0.0
