import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Header, Depends
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse, UserAuth, Token
from auth import hash_password, verify_password, create_access_token, decode_token
from chat_engine import get_response, clear_session
from crises import is_crisis_message, SAFETY_MESSAGE
from logger import log_chat
from memory_store import (
    init_db,
    save_message,
    get_recent_history,
    get_all_sessions,
    get_session_messages,
    create_user,
    get_user,
    get_admin_stats
)

load_dotenv()

# We will init_db() inside the startup event to avoid blocking module load
# init_db() moved to @app.on_event("startup")

app = FastAPI(
    title="MindEase — AI-Powered Mental Health Chatbot API",
    description="Mental health companion securely powered by Gemini UI and MongoDB",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(authorization: str = Header(None)):
    """Extracts username from JWT token. Uses 'anonymous' if no token."""
    if not authorization or not authorization.startswith("Bearer "):
        return "anonymous"
    token = authorization.split(" ")[1]
    username = decode_token(token)
    if not username:
        return "anonymous"
    return username


@app.get("/")
def read_root():
    return {"message": "Welcome to MindEase — AI-Powered Mental Health Chatbot API 🌿"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── Auth Routes ────────────────────────────────────────────────────────

@app.post("/register")
def register(user: UserAuth):
    if not create_user(user.username, hash_password(user.password)):
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User registered successfully"}


@app.post("/login", response_model=Token)
def login(user: UserAuth):
    db_user = get_user(user.username)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer", "username": user.username}


# ── Chat Routes ────────────────────────────────────────────────────────

@app.get("/sessions")
def list_sessions(username: str = Depends(get_current_user)):
    return get_all_sessions(username)


@app.get("/sessions/{session_id}")
def read_session(session_id: str, username: str = Depends(get_current_user)):
    return get_session_messages(session_id, username)


@app.post("/chat", response_model=ChatResponse)
def chat_with_memory(request: ChatRequest, username: str = Depends(get_current_user)):
    session_id = request.session_id or str(uuid4())
    user_query = request.query.strip() if request.query else ""

    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if len(user_query) > 2000:
        raise HTTPException(status_code=400, detail="Query is too long.")

    # Crisis keyword check — safety net before AI
    is_crisis = is_crisis_message(user_query)
    
    if is_crisis:
        save_message(session_id, "user", user_query, username, is_crisis=False)
        save_message(session_id, "bot", SAFETY_MESSAGE, username, is_crisis=True)
        log_chat(session_id, user_query, SAFETY_MESSAGE, True)
        
        return ChatResponse(response=SAFETY_MESSAGE, session_id=session_id, is_crisis=True)

    # Load recent history for context
    history = get_recent_history(session_id, limit=20)

    # Generate AI response
    try:
        response = get_response(session_id, user_query, history)
    except Exception as e:
        print(f"[MindEase] Error generating response: {e}")
        response = "I'm having a little trouble thinking right now, but I'm still here for you. 💚\n\nCould you try sending your message again?"

    # Save to MongoDB Database securely tied to the user
    save_message(session_id, "user", user_query, username)
    save_message(session_id, "bot", response, username)
    log_chat(session_id, user_query, response, False)

    return ChatResponse(
        response=response,
        session_id=session_id,
        is_crisis=False,
    )


@app.on_event("startup")
async def startup_event():
    print("[MindEase] Backend server is starting up...")
    try:
        init_db()
        print("[MindEase] MongoDB connection initialized successfully.")
    except Exception as e:
        print(f"[MindEase] CRITICAL: FAILED to connect to MongoDB: {e}")
        print("[MindEase] Please check your MONGO_URI and IP whitelist in Atlas.")

@app.post("/chat/new")
def new_chat():
    new_session_id = str(uuid4())
    clear_session(new_session_id)
    return {"session_id": new_session_id}


# ── Admin Routes ───────────────────────────────────────────────────────

@app.get("/admin/stats")
def admin_stats(username: str = Depends(get_current_user)):
    if username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin only.")
    return get_admin_stats()