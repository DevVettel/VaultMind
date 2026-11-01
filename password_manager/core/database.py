import os
import shutil
import sqlite3
import sys
from datetime import datetime
from typing import Optional, Tuple


def _default_data_dir() -> str:
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "VaultMind")
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", home), "VaultMind")
    return os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share")), "VaultMind")


def _resolve_db_path() -> str:
    override = os.environ.get("VAULTMIND_DB_PATH")
    if override:
        os.makedirs(os.path.dirname(os.path.abspath(override)), exist_ok=True)
        return override

    legacy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vaultmind.db")
    data_dir = _default_data_dir()
    db_path = os.path.join(data_dir, "vaultmind.db")

    os.makedirs(data_dir, exist_ok=True)
    if os.path.exists(legacy_path) and not os.path.exists(db_path):
        shutil.copy2(legacy_path, db_path)

    return db_path


DB_PATH: Optional[str] = None


def get_db_path() -> str:
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = _resolve_db_path()
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT NOT NULL,
                encrypted_password TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    _migrate_db()


def _migrate_db():
    with get_connection() as conn:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(passwords)").fetchall()}
        if "url" not in cols:
            conn.execute("ALTER TABLE passwords ADD COLUMN url TEXT DEFAULT ''")
        if "notes" not in cols:
            conn.execute("ALTER TABLE passwords ADD COLUMN notes TEXT DEFAULT ''")
        if "is_favorite" not in cols:
            conn.execute("ALTER TABLE passwords ADD COLUMN is_favorite INTEGER DEFAULT 0")
        if "last_used_at" not in cols:
            conn.execute("ALTER TABLE passwords ADD COLUMN last_used_at TEXT DEFAULT NULL")
        conn.commit()


def is_first_launch() -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key='salt'").fetchone()
        return row is None


def store_master_credentials(salt: bytes, verifier: str):
    """Store the salt and verifier token; drops any legacy password hash."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('salt', ?)",
            (salt.hex(),)
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('verifier', ?)",
            (verifier,)
        )
        conn.execute("DELETE FROM meta WHERE key='hash'")
        conn.commit()


def get_master_credentials() -> Tuple[bytes, Optional[str], Optional[str]]:
    """Return (salt, verifier, legacy_hash); either of the last two may be None."""
    with get_connection() as conn:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta").fetchall()}
    return bytes.fromhex(meta["salt"]), meta.get("verifier"), meta.get("hash")


def add_password(title: str, username: str, encrypted_password: str, category: str,
                 url: str = '', notes: str = '') -> int:
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO passwords
               (title, username, encrypted_password, category, url, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, username, encrypted_password, category, url, notes, now, now)
        )
        conn.commit()
        return cursor.lastrowid


def update_password(record_id: int, title: str, username: str, encrypted_password: str,
                    category: str, url: str = '', notes: str = ''):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            """UPDATE passwords
               SET title=?, username=?, encrypted_password=?, category=?, url=?, notes=?, updated_at=?
               WHERE id=?""",
            (title, username, encrypted_password, category, url, notes, now, record_id)
        )
        conn.commit()


def delete_password(record_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM passwords WHERE id=?", (record_id,))
        conn.commit()


def toggle_favorite(record_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE passwords SET is_favorite = CASE WHEN is_favorite=1 THEN 0 ELSE 1 END WHERE id=?",
            (record_id,)
        )
        conn.commit()


def update_last_used(record_id: int):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute("UPDATE passwords SET last_used_at=? WHERE id=?", (now, record_id))
        conn.commit()


def get_password(record_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM passwords WHERE id=?", (record_id,)).fetchone()


def get_all_passwords(category: Optional[str] = None) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if category == "Favorites":
            return conn.execute(
                "SELECT * FROM passwords WHERE is_favorite=1 ORDER BY title"
            ).fetchall()
        elif category == "Recent":
            return conn.execute(
                "SELECT * FROM passwords WHERE last_used_at IS NOT NULL ORDER BY last_used_at DESC LIMIT 5"
            ).fetchall()
        elif category and category != "All":
            return conn.execute(
                "SELECT * FROM passwords WHERE category=? ORDER BY is_favorite DESC, title",
                (category,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM passwords ORDER BY is_favorite DESC, title"
        ).fetchall()


def get_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT category FROM passwords ORDER BY category").fetchall()
        return [r["category"] for r in rows]


def search_passwords(query: str) -> list[sqlite3.Row]:
    like = f"%{query.lower()}%"
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM passwords
               WHERE LOWER(title) LIKE ?
                  OR LOWER(username) LIKE ?
                  OR LOWER(category) LIKE ?
                  OR LOWER(COALESCE(url,'')) LIKE ?
                  OR LOWER(COALESCE(notes,'')) LIKE ?
               ORDER BY is_favorite DESC, title""",
            (like, like, like, like, like)
        ).fetchall()


def count_passwords() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM passwords").fetchone()[0]
