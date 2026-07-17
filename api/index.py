"""FastAPI surface for the insurance RAG chatbot.

Run:  .venv\\Scripts\\python -m uvicorn api.index:app --reload --port 8020
UI:   http://127.0.0.1:8020/        Docs: http://127.0.0.1:8020/docs

The `role` field simulates the SSO entitlement claims from the system
design — in production it would come from the OIDC token, never the client.
"""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.graph import ask

app = FastAPI(title="Acme Mutual — Agent Knowledge Assistant", version="1.0.0")

_INDEX_HTML = (Path(__file__).resolve().parent.parent / "ui" / "index.html").read_text(encoding="utf-8")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    role: Literal["agent_personal", "agent_commercial", "claims", "underwriter"] = "agent_personal"
    licensed_states: list[str] = ["TX"]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return _INDEX_HTML


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "insurance-rag-chatbot"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    return ask(request.question, {
        "role": request.role,
        "licensed_states": [s.upper() for s in request.licensed_states],
    })
