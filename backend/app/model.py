import os

import httpx
from fastapi import HTTPException

MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:1b")


def reply(messages):
    try:
        response = httpx.post(
            os.getenv("OLLAMA_URL", "http://model:11434") + "/api/chat",
            json={"model": MODEL_NAME, "messages": messages, "stream": False,
                  "options": {"num_predict": 512, "num_ctx": 4096}},
            timeout=180,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Empty model response")
        return content
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(503, "The local model is unavailable or timed out. Please retry.") from exc
