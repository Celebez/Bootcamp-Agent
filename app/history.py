"""Persistensi sesi/riwayat percakapan (SQLite).

- Tabel `sessions(id, title, created_at, updated_at, model)`.
- Tabel `messages(id, session_id, role, content, created_at)`.
- `~/.bootcamp/history.db` (override via BOOTCAMP_HOME).

Ringan: pakai sqlite3 stdlib (tidak ada dep tambahan). Aman untuk VPS & Termux.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterable, List, Optional


def _home() -> str:
    return os.environ.get("BOOTCAMP_HOME") or os.path.join(
        os.path.expanduser("~"), ".bootcamp"
    )


def _db_path() -> str:
    return os.path.join(_home(), "history.db")


@contextmanager
def _conn():
    os.makedirs(_home(), exist_ok=True)
    c = sqlite3.connect(_db_path())
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    _migrate(c)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def _migrate(c: sqlite3.Connection) -> None:
    c.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            model TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )"""
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)"
    )


@dataclass
class Session:
    id: str
    title: str
    model: Optional[str]
    created_at: float
    updated_at: float

    def short_id(self) -> str:
        return self.id[:8]


def list_sessions(limit: int = 20) -> List[Session]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, title, model, created_at, updated_at "
            "FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [Session(*r) for r in rows]


def get_session(session_id: str) -> Optional[Session]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, title, model, created_at, updated_at FROM sessions WHERE id=?",
            (session_id,),
        ).fetchone()
    return Session(*row) if row else None


def create_session(title: str, model: Optional[str] = None) -> Session:
    sid = uuid.uuid4().hex
    now = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (id, title, model, created_at, updated_at) VALUES (?,?,?,?,?)",
            (sid, title or "tanpa-judul", model, now, now),
        )
    return Session(sid, title or "tanpa-judul", model, now, now)


def append_message(session_id: str, role: str, content: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
            (session_id, role, content, time.time()),
        )
        c.execute(
            "UPDATE sessions SET updated_at=? WHERE id=?", (time.time(), session_id)
        )


def load_messages(session_id: str, limit: Optional[int] = None) -> List[dict]:
    with _conn() as c:
        if limit:
            rows = c.execute(
                "SELECT role, content FROM messages WHERE session_id=? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            rows.reverse()
        else:
            rows = c.execute(
                "SELECT role, content FROM messages WHERE session_id=? ORDER BY id",
                (session_id,),
            ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def search_sessions(query: str, limit: int = 20) -> List[Session]:
    """Cari sesi yang title-nya mengandung query (case-insensitive)."""
    like = f"%{query}%"
    with _conn() as c:
        rows = c.execute(
            "SELECT id, title, model, created_at, updated_at FROM sessions "
            "WHERE title LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (like, limit),
        ).fetchall()
    return [Session(*r) for r in rows]


def delete_session(session_id: str) -> bool:
    with _conn() as c:
        cur = c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    return cur.rowcount > 0


def rename_session(session_id: str, new_title: str) -> bool:
    with _conn() as c:
        cur = c.execute(
            "UPDATE sessions SET title=? WHERE id=?", (new_title, session_id)
        )
    return cur.rowcount > 0


def export_session(session_id: str) -> Optional[dict]:
    s = get_session(session_id)
    if not s:
        return None
    msgs = load_messages(session_id)
    return {
        "session": {
            "id": s.id,
            "title": s.title,
            "model": s.model,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        },
        "messages": msgs,
    }
