from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tutor_model import get_tutor_reply, ChatTurn

app = FastAPI(title="AI Tutor Model Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryTurn(BaseModel):
    role: str = Field(..., description="'user' or 'model'")
    text: str


class ChatRequest(BaseModel):
    history: List[HistoryTurn] = Field(
        default_factory=list,
        description="Prior conversation turns, oldest first. Empty on first message.",
    )
    message: str = Field(..., description="The learner's new message.")


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    """Simple liveness check for the backend / deployment platform to ping."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main endpoint. The backend sends conversation history + the learner's
    newest message, and receives the tutor's reply.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    history: List[ChatTurn] = [
        {"role": turn.role, "text": turn.text} for turn in request.history
    ]

    try:
        reply = get_tutor_reply(history, request.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model call failed: {str(e)}")

    return ChatResponse(reply=reply)