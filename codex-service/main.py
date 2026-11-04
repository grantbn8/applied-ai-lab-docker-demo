"""Private Compose adapter for ChatGPT-authenticated, text-only Codex calls."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Headless Codex adapter")
run_lock = threading.Lock()
LOGIN_HELP = "ChatGPT sign-in required. Run: docker compose exec codex codex login --device-auth"


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=32000)


class ChatInput(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=21)


def signed_in():
    # Inspect only the authentication type; never return or log tokens.
    try:
        auth = json.loads((Path(os.environ["CODEX_HOME"]) / "auth.json").read_text())
        return auth.get("auth_mode") == "chatgpt" and bool(auth.get("tokens"))
    except (OSError, ValueError):
        return False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return {"authenticated": signed_in(), "provider": "chatgpt"}


@app.post("/chat")
def chat(body: ChatInput):
    if not signed_in():
        raise HTTPException(503, LOGIN_HELP)
    if not run_lock.acquire(blocking=False):
        raise HTTPException(409, "ChatGPT is answering another request. Please retry shortly.")
    try:
        with tempfile.TemporaryDirectory(prefix="chat-", dir="/workspace") as directory:
            output = Path(directory) / "answer.txt"
            command = [
                "codex", "exec", "--skip-git-repo-check", "--ephemeral",
                "--sandbox", "read-only", "--cd", directory,
                "-c", 'forced_login_method="chatgpt"',
                "-c", 'cli_auth_credentials_store="file"',
                "-c", 'approval_policy="never"',
                "-c", 'web_search="disabled"',
                "-c", 'features.shell_tool=false',
                "-c", 'features.unified_exec=false',
                "-c", 'features.multi_agent=false',
                "-c", 'features.apps=false',
                "-c", 'features.remote_plugin=false',
                "-c", 'features.browser_use=false',
                "-c", 'features.computer_use=false',
                "-c", 'features.image_generation=false',
                "-c", 'features.hooks=false',
                "-c", 'developer_instructions="You are a concise conversational assistant. Answer the last user message in the supplied conversation. Do not use tools, inspect files, or execute commands. Use Markdown when useful."',
                "--output-last-message", str(output), "-",
            ]
            # No API-key authentication or inherited provider overrides.
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith(("OPENAI_", "CODEX_API_"))}
            prompt = "Conversation (JSON):\n" + json.dumps(
                [message.model_dump() for message in body.messages])
            try:
                result = subprocess.run(command, input=prompt, text=True,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                        env=environment, timeout=170)
            except subprocess.TimeoutExpired as exc:
                raise HTTPException(504, "ChatGPT timed out. Please retry.") from exc
            if result.returncode != 0 or not output.exists():
                # CLI diagnostics may contain private context; do not expose them.
                raise HTTPException(503, "Codex could not respond. Check ChatGPT sign-in and account usage limits, then retry.")
            answer = output.read_text().strip()
            if not answer:
                raise HTTPException(503, "ChatGPT returned an empty response. Please retry.")
            return {"content": answer}
    finally:
        run_lock.release()
