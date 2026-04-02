import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse
from chat_engine import get_response, clear_session
from crises import is_crisis_message, SAFETY_MESSAGE
from logger import log_chat
from memory_store import (
    init_db,
    save_message,
    get_recent_history,
    get_all_sessions,
    get_session_messages,
)

load_dotenv()

init_db()

app = FastAPI(
    title="MindEase — Mental Health Chatbot API",
    description="AI-powered mental health companion using Gemini",
    version="2.0.0",
)

# Allow CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to MindEase — AI-Powered Mental Health Chatbot API 🌿"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/sessions")
def list_sessions():
    return get_all_sessions()


@app.get("/sessions/{session_id}")
def read_session(session_id: str):
    return get_session_messages(session_id)


@app.post("/chat", response_model=ChatResponse)
def chat_with_memory(request: ChatRequest):
    session_id = request.session_id or str(uuid4())
    user_query = request.query.strip() if request.query else ""

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if len(user_query) > 2000:
        raise HTTPException(status_code=400, detail="Query is too long (max 2000 characters).")

    # Crisis keyword check — safety net before AI
    if is_crisis_message(user_query):
        save_message(session_id, "user", user_query)
        save_message(session_id, "bot", SAFETY_MESSAGE)

        log_chat(
            session_id=session_id,
            query=user_query,
            response=SAFETY_MESSAGE,
            is_crisis=True,
        )
        return ChatResponse(
            response=SAFETY_MESSAGE,
            session_id=session_id,
            is_crisis=True,
        )

    # Load recent history for context
    history = get_recent_history(session_id, limit=20)

    # Generate AI response with conversation history
    try:
        response = get_response(session_id, user_query, history)
    except Exception as e:
        print(f"[MindEase] Error generating response: {e}")
        response = (
            "I'm having a little trouble thinking right now, but I'm still here for you. 💚\n\n"
            "Could you try sending your message again?"
        )

    # Save current messages to DB
    save_message(session_id, "user", user_query)
    save_message(session_id, "bot", response)

    log_chat(
        session_id=session_id,
        query=user_query,
        response=response,
        is_crisis=False,
    )

    return ChatResponse(
        response=response,
        session_id=session_id,
        is_crisis=False,
    )


@app.post("/chat/new")
def new_chat():
    """Create a fresh session and clear any cached AI context."""
    new_session_id = str(uuid4())
    clear_session(new_session_id)
    return {"session_id": new_session_id}