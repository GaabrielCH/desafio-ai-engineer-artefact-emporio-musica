"""Persistência de histórico de conversas e rastreamento de chamadas de ferramentas (SQLite)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import settings


class ConversationMemory:
    """Armazena histórico de mensagens e traces de ferramentas por sessão em SQLite."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else settings.chat_history_db
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Registra uma mensagem (user ou assistant) e as ferramentas acionadas."""
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (session_id, role, content, tool_calls_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Recupera as últimas mensagens da sessão em ordem cronológica."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT role, content, tool_calls_json, created_at
            FROM (
                SELECT id, role, content, tool_calls_json, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (session_id, limit),
        )
        rows = cur.fetchall()
        result: list[dict[str, Any]] = []
        for r in rows:
            tc = json.loads(r["tool_calls_json"]) if r["tool_calls_json"] else []
            result.append(
                {
                    "role": r["role"],
                    "content": r["content"],
                    "tool_calls": tc,
                    "created_at": r["created_at"],
                }
            )
        return result

    def clear_session(self, session_id: str) -> None:
        """Apaga o histórico de uma sessão específica."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.commit()
