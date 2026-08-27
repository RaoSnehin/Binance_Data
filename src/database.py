"""
CryptoSphere — Database Module (SQLite)
Provides persistent storage for portfolio holdings.

The database is a local SQLite file: `cryptosphere.db` in the project root.
No server, no configuration — just a file that persists across refreshes and restarts.

Schema:
  Table: portfolio
    id          INTEGER PRIMARY KEY AUTOINCREMENT
    coin        TEXT NOT NULL          -- e.g. "Bitcoin"
    qty         REAL NOT NULL          -- quantity held
    buy_price   REAL NOT NULL          -- price at time of purchase (USD)
    added_at    TEXT NOT NULL          -- ISO timestamp
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict

# ── Database path ──────────────────────────────────────────────────────────────
# Stored in project root so it's easy to find and backup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cryptosphere.db")


# ── Connection helper ──────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ── Initialisation ─────────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create the database and tables if they don't exist.
    Safe to call multiple times (idempotent).
    """
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                coin        TEXT    NOT NULL,
                qty         REAL    NOT NULL,
                buy_price   REAL    NOT NULL,
                added_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# ── Portfolio CRUD ─────────────────────────────────────────────────────────────

def add_position(coin: str, qty: float, buy_price: float) -> int:
    """
    Insert a new portfolio position. Returns the new row ID.
    """
    now = datetime.now().isoformat(timespec="seconds")
    with _get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO portfolio (coin, qty, buy_price, added_at) VALUES (?, ?, ?, ?)",
            (coin, qty, buy_price, now),
        )
        conn.commit()
        return cur.lastrowid


def get_all_positions() -> List[Dict]:
    """
    Return all portfolio positions as a list of dicts.
    Ordered by insertion time (oldest first).
    """
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT id, coin, qty, buy_price, added_at FROM portfolio ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_position(row_id: int) -> None:
    """Delete a single position by its row ID."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM portfolio WHERE id = ?", (row_id,))
        conn.commit()


def clear_all_positions() -> None:
    """Delete ALL portfolio positions (used by 'Clear Portfolio' button)."""
    with _get_connection() as conn:
        conn.execute("DELETE FROM portfolio")
        conn.commit()


def update_position(row_id: int, qty: float, buy_price: float) -> None:
    """Update qty and buy_price for an existing position."""
    with _get_connection() as conn:
        conn.execute(
            "UPDATE portfolio SET qty = ?, buy_price = ? WHERE id = ?",
            (qty, buy_price, row_id),
        )
        conn.commit()


def get_db_info() -> Dict:
    """Return metadata about the database (path, size, row count)."""
    count = 0
    try:
        with _get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM portfolio").fetchone()[0]
    except Exception:
        pass
    size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "path": DB_PATH,
        "size_kb": round(size_bytes / 1024, 2),
        "position_count": count,
    }


# ── Auto-init on import ────────────────────────────────────────────────────────
# The DB and table are created automatically the first time this module is imported.
init_db()
