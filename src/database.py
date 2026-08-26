"""
FinLegal-Chat Ultimate - SQLite Database Manager
Handles chat sessions, messages, and document tracking.
"""

import os
import sqlite3
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


class DatabaseManager:
    """Thread-safe SQLite database for persistent chat history and document tracking."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        return self._local.connection

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0,
                document_count INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                chart_data TEXT,
                reports TEXT,
                created_at TEXT NOT NULL,
                agent_sources TEXT DEFAULT '[]',
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                file_type TEXT,
                chunk_count INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
        """)

        # Initialize schema version
        conn.execute(
            "INSERT OR IGNORE INTO app_state (key, value, updated_at) VALUES (?, ?, ?)",
            ("schema_version", str(self.SCHEMA_VERSION), datetime.now().isoformat()),
        )
        conn.commit()

    # --- Session Operations ---

    def create_session(self, title: str = None) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title or "New Chat", now, now),
        )
        conn.commit()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID."""
        conn = self._get_connection()
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def list_sessions(
        self,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """List sessions ordered by most recent update."""
        conn = self._get_connection()
        query = "SELECT * FROM sessions"
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY is_pinned DESC, updated_at DESC LIMIT ? OFFSET ?"
        rows = conn.execute(query, (limit, offset)).fetchall()
        return [dict(r) for r in rows]

    def update_session_title(self, session_id: str, title: str):
        """Update session title."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now().isoformat(), session_id),
        )
        conn.commit()

    def toggle_pin_session(self, session_id: str):
        """Toggle pin status of a session."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET is_pinned = CASE WHEN is_pinned = 1 THEN 0 ELSE 1 END, "
            "updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id),
        )
        conn.commit()

    def archive_session(self, session_id: str):
        """Archive a session."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET is_archived = 1, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), session_id),
        )
        conn.commit()

    def delete_session(self, session_id: str):
        """Delete a session and all related messages."""
        conn = self._get_connection()
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM documents WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

    def search_sessions(self, query: str, limit: int = 20) -> List[Dict]:
        """Search sessions by title or message content."""
        conn = self._get_connection()
        search_term = f"%{query}%"
        rows = conn.execute(
            """SELECT DISTINCT s.* FROM sessions s
               LEFT JOIN messages m ON m.session_id = s.id
               WHERE (s.title LIKE ? OR m.content LIKE ?) AND s.is_archived = 0
               ORDER BY s.updated_at DESC LIMIT ?""",
            (search_term, search_term, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Message Operations ---

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        chart_data: Dict = None,
        reports: Dict = None,
        agent_sources: List[str] = None,
    ) -> str:
        """Add a message to a session."""
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO messages 
               (id, session_id, role, content, chart_data, reports, created_at, agent_sources)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                msg_id,
                session_id,
                role,
                content,
                json.dumps(chart_data) if chart_data else None,
                json.dumps(reports) if reports else None,
                now,
                json.dumps(agent_sources or []),
            ),
        )
        # Update session counters
        conn.execute(
            """UPDATE sessions SET 
               message_count = (SELECT COUNT(*) FROM messages WHERE session_id = ?),
               updated_at = ?
               WHERE id = ?""",
            (session_id, now, session_id),
        )
        conn.commit()
        return msg_id

    def get_messages(self, session_id: str, limit: int = 200) -> List[Dict]:
        """Get all messages for a session."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        result = []
        for r in rows:
            msg = dict(r)
            if msg.get("chart_data"):
                try:
                    msg["chart_data"] = json.loads(msg["chart_data"])
                except (json.JSONDecodeError, TypeError):
                    msg["chart_data"] = None
            if msg.get("reports"):
                try:
                    msg["reports"] = json.loads(msg["reports"])
                except (json.JSONDecodeError, TypeError):
                    msg["reports"] = None
            if msg.get("agent_sources"):
                try:
                    msg["agent_sources"] = json.loads(msg["agent_sources"])
                except (json.JSONDecodeError, TypeError):
                    msg["agent_sources"] = []
            result.append(msg)
        return result

    def get_last_n_messages(self, session_id: str, n: int = 10) -> List[Dict]:
        """Get the last N messages for context window."""
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT role, content FROM messages 
               WHERE session_id = ? ORDER BY created_at DESC LIMIT ?""",
            (session_id, n),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # --- Document Operations ---

    def add_document(
        self,
        filename: str,
        file_path: str,
        file_size: int = 0,
        file_type: str = None,
        chunk_count: int = 0,
        session_id: str = None,
    ) -> str:
        """Register an uploaded document."""
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO documents 
               (id, session_id, filename, file_path, file_size, file_type, chunk_count, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, session_id, filename, file_path, file_size, file_type, chunk_count, now),
        )
        if session_id:
            conn.execute(
                """UPDATE sessions SET 
                   document_count = (SELECT COUNT(*) FROM documents WHERE session_id = ?),
                   updated_at = ?
                   WHERE id = ?""",
                (session_id, now, session_id),
            )
        conn.commit()
        return doc_id

    def get_documents(self, session_id: str = None) -> List[Dict]:
        """Get documents, optionally filtered by session."""
        conn = self._get_connection()
        if session_id:
            rows = conn.execute(
                "SELECT * FROM documents WHERE session_id = ? ORDER BY uploaded_at DESC",
                (session_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY uploaded_at DESC LIMIT 100"
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_document(self, doc_id: str):
        """Remove a document record."""
        conn = self._get_connection()
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()

    # --- State Operations ---

    def set_state(self, key: str, value: str):
        """Set an application state value."""
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat()),
        )
        conn.commit()

    def get_state(self, key: str, default: str = None) -> Optional[str]:
        """Get an application state value."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def get_stats(self) -> Dict[str, int]:
        """Get application statistics."""
        conn = self._get_connection()
        sessions = conn.execute("SELECT COUNT(*) as c FROM sessions WHERE is_archived = 0").fetchone()["c"]
        messages = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
        documents = conn.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]
        return {"sessions": sessions, "messages": messages, "documents": documents}

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


import json
