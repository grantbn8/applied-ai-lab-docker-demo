import os

import httpx
from fastapi import HTTPException

from .model import MODEL_NAME, reply as local_reply

CODEX_URL = os.getenv("CODEX_URL", "http://codex:8001")


def provider_status():
    authenticated = False
    reachable = False
    try:
        response = httpx.get(CODEX_URL + "/status", timeout=3)
        response.raise_for_status()
        authenticated = response.json().get("authenticated", False)
        reachable = True
    except (httpx.HTTPError, ValueError):
        pass
    return {"local_model": MODEL_NAME, "chatgpt_authenticated": authenticated,
            "chatgpt_reachable": reachable}


def reply(messages, provider):
    # Database metadata is not part of the model conversation payload.
    messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    if provider == "local":
        return local_reply(messages)
    try:
        response = httpx.post(CODEX_URL + "/chat", json={"messages": messages}, timeout=180)
        if response.status_code in (409, 503, 504):
            raise HTTPException(response.status_code, response.json()["detail"])
        response.raise_for_status()
        return response.json()["content"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise HTTPException(503, "The ChatGPT service is unavailable. Please retry or select Local.") from exc
