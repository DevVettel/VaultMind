import sqlite3
import os
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vaultmind.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
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


def is_first_launch() -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key='salt'").fetchone()
        return row is None


def store_master_credentials(salt: bytes, password_hash: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('salt', ?)",
            (salt.hex(),)
        )
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('hash', ?)",
            (password_hash,)
        )
        conn.commit()


def get_master_credentials() -> tuple[bytes, str]:
    with get_connection() as conn:
        salt_hex = conn.execute("SELECT value FROM meta WHERE key='salt'").fetchone()["value"]
        pwd_hash = conn.execute("SELECT value FROM meta WHERE key='hash'").fetchone()["value"]
    return bytes.fromhex(salt_hex), pwd_hash


def add_password(title: str, username: str, encrypted_password: str, category: str) -> int:
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO passwords (title, username, encrypted_password, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, username, encrypted_password, category, now, now)
        )
        conn.commit()
        return cursor.lastrowid


def update_password(record_id: int, title: str, username: str, encrypted_password: str, category: str):
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE passwords SET title=?, username=?, encrypted_password=?, category=?, updated_at=? WHERE id=?",
            (title, username, encrypted_password, category, now, record_id)
        )
        conn.commit()


def delete_password(record_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM passwords WHERE id=?", (record_id,))
        conn.commit()


def get_all_passwords(category: Optional[str] = None) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if category and category != "All":
            return conn.execute(
                "SELECT * FROM passwords WHERE category=? ORDER BY title",
                (category,)
            ).fetchall()
        return conn.execute("SELECT * FROM passwords ORDER BY title").fetchall()


def get_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT category FROM passwords ORDER BY category").fetchall()
        return [r["category"] for r in rows]


def search_passwords(query: str) -> list[sqlite3.Row]:
    like = f"%{query}%"
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM passwords WHERE title LIKE ? OR username LIKE ? OR category LIKE ? ORDER BY title",
            (like, like, like)
        ).fetchall()


def count_passwords() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM passwords").fetchone()[0]
