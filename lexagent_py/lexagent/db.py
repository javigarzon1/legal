"""Persistencia local con SQLite."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any

DB_PATH = os.environ.get("LEXAGENT_DB", "lexagent.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                doc_type TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                form_fields TEXT NOT NULL,      -- JSON array
                knowledge_base TEXT NOT NULL,   -- texto plano consolidado
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS validations (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                form_data TEXT NOT NULL,        -- JSON
                report_md TEXT,
                document_md TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            );
            """
        )


def create_agent(
    *,
    name: str,
    description: str,
    doc_type: str,
    system_prompt: str,
    form_fields: list[dict[str, Any]],
    knowledge_base: str,
) -> str:
    aid = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            "INSERT INTO agents VALUES (?,?,?,?,?,?,?,?)",
            (
                aid,
                name,
                description,
                doc_type,
                system_prompt,
                json.dumps(form_fields, ensure_ascii=False),
                knowledge_base,
                datetime.utcnow().isoformat(),
            ),
        )
    return aid


def list_agents() -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, description, doc_type, created_at FROM agents ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_agent(agent_id: str) -> dict[str, Any] | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["form_fields"] = json.loads(d["form_fields"])
    return d


def delete_agent(agent_id: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM validations WHERE agent_id = ?", (agent_id,))
        c.execute("DELETE FROM agents WHERE id = ?", (agent_id,))


def save_validation(
    *, agent_id: str, form_data: dict[str, Any], report_md: str, document_md: str
) -> str:
    vid = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            "INSERT INTO validations VALUES (?,?,?,?,?,?)",
            (
                vid,
                agent_id,
                json.dumps(form_data, ensure_ascii=False),
                report_md,
                document_md,
                datetime.utcnow().isoformat(),
            ),
        )
    return vid


def list_validations(agent_id: str) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at FROM validations WHERE agent_id = ? ORDER BY created_at DESC",
            (agent_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_validation(vid: str) -> dict[str, Any] | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM validations WHERE id = ?", (vid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["form_data"] = json.loads(d["form_data"])
    return d
