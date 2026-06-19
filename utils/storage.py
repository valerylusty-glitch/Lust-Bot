"""
Gestion de la base de données SQLite : historique des téléchargements
et statistiques d'utilisation du bot. Toutes les opérations sont protégées
par try/except pour ne jamais faire planter le bot en cas d'erreur disque.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from contextlib import contextmanager

from config import DB_PATH

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Crée les tables nécessaires si elles n'existent pas encore."""
    try:
        with get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    platform TEXT,
                    title TEXT,
                    url TEXT,
                    size_mb REAL,
                    duration TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_seen TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"init_db error: {e}")


def register_user(user_id: int, username: str):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_seen) VALUES (?, ?, ?)",
                (user_id, username, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"register_user error: {e}")


def add_download(user_id: int, username: str, platform: str, title: str,
                  url: str, size_mb: float, duration: str):
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO downloads
                   (user_id, username, platform, title, url, size_mb, duration, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, platform, title, url, size_mb, duration,
                 datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"add_download error: {e}")


def get_user_history(user_id: int, limit: int = 10):
    try:
        with get_connection() as conn:
            cur = conn.execute(
                """SELECT platform, title, created_at FROM downloads
                   WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
                (user_id, limit),
            )
            return cur.fetchall()
    except Exception as e:
        logger.error(f"get_user_history error: {e}")
        return []


def get_global_stats():
    try:
        with get_connection() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_downloads = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
            top_row = conn.execute(
                """SELECT platform, COUNT(*) c FROM downloads
                   GROUP BY platform ORDER BY c DESC LIMIT 1"""
            ).fetchone()
            top_platform = top_row[0] if top_row else "—"
            return {
                "total_users": total_users,
                "total_downloads": total_downloads,
                "top_platform": top_platform,
            }
    except Exception as e:
        logger.error(f"get_global_stats error: {e}")
        return {"total_users": 0, "total_downloads": 0, "top_platform": "—"}


def get_user_download_count(user_id: int) -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM downloads WHERE user_id = ?", (user_id,))
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"get_user_download_count error: {e}")
        return 0

