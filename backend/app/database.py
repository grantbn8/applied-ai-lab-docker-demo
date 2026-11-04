from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def connect():
    # libpq reads the PG* environment variables configured by Compose.
    return psycopg.connect("", row_factory=dict_row)


def initialize():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                title TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS messages_conversation_idx
                ON messages (conversation_id, id);
        """)
        for migration in sorted((Path(__file__).parent.parent / "migrations").glob("*.sql")):
            conn.execute(migration.read_text())


def messages_for(conn, conversation_id):
    return conn.execute(
        "SELECT role, content, provider FROM messages WHERE conversation_id = %s ORDER BY id",
        (conversation_id,),
    ).fetchall()
