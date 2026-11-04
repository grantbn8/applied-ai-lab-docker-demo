from uuid import UUID, uuid4
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from .database import connect, messages_for
from .model import MODEL_NAME
from .providers import reply, provider_status

router = APIRouter(prefix="/api")


class MessageInput(BaseModel):
    provider: Literal["local", "chatgpt"] = "local"
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()


@router.get("/health")
def health():
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok", "model": MODEL_NAME}


@router.get("/providers")
def providers():
    return provider_status()


@router.get("/conversations")
def list_conversations(q: str = Query(default="", max_length=200)):
    # Escape LIKE metacharacters so search treats input as literal text.
    term = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    with connect() as conn:
        return conn.execute("""
            SELECT c.* FROM conversations c
            WHERE c.title ILIKE %s OR EXISTS (
                SELECT 1 FROM messages m
                WHERE m.conversation_id = c.id AND m.content ILIKE %s
            ) ORDER BY c.updated_at DESC
        """, (f"%{term}%", f"%{term}%")).fetchall()


@router.post("/conversations", status_code=201)
def create_conversation():
    with connect() as conn:
        return conn.execute(
            "INSERT INTO conversations (id, title) VALUES (%s, %s) RETURNING *",
            (uuid4(), "New conversation"),
        ).fetchone()


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: UUID):
    with connect() as conn:
        conversation = conn.execute(
            "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
        ).fetchone()
        if not conversation:
            raise HTTPException(404, "Conversation not found")
        return {**conversation, "messages": messages_for(conn, conversation_id)}


@router.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: UUID, body: MessageInput):
    with connect() as conn:
        # One in-flight exchange per conversation, including across backend workers.
        if not conn.execute("SELECT pg_try_advisory_xact_lock(hashtext(%s)) AS locked",
                            (str(conversation_id),)).fetchone()["locked"]:
            raise HTTPException(409, "This conversation is already generating a reply.")
        conversation = conn.execute(
            "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
        ).fetchone()
        if not conversation:
            raise HTTPException(404, "Conversation not found")
        history = messages_for(conn, conversation_id)
        user_message = {"role": "user", "content": body.content}
        answer = reply(history[-20:] + [user_message], body.provider)
        # Commit the pair together; failed inference leaves history unchanged.
        for message in [user_message, {"role": "assistant", "content": answer}]:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, provider) VALUES (%s, %s, %s, %s)",
                (conversation_id, message["role"], message["content"], body.provider),
            )
        title = body.content[:70] if not history else conversation["title"]
        conn.execute("UPDATE conversations SET title = %s, updated_at = now() WHERE id = %s",
                     (title, conversation_id))
        return {"id": conversation_id, "title": title,
                "messages": messages_for(conn, conversation_id)}
