"""
chat_engine.py — Robust Professional AI.
Finds the correct model name automatically and provides pro-level interaction.
"""

import os
import cohere
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

SYSTEM_PROMPT = """You are **Sage 🌿**, a world-class AI mental health companion. You speak with deep empathy and professional wisdom. Use markdown. Focus on CBT and mindfulness."""

_client = None

def _get_client():
    global _client
    if _client is None and COHERE_API_KEY:
        _client = cohere.Client(api_key=COHERE_API_KEY)
    return _client

MODEL_CANDIDATES = [
    "command-r-08-2024",
    "command-r-plus-08-2024",
    "command-nightly",
    "command",
    "command-light"
]

def get_response(session_id: str, user_query: str, history: list = None) -> str:
    if not COHERE_API_KEY:
        return _fallback_response(user_query)

    client = _get_client()
    co_history = []
    if history:
        for h in history[-10:]:
            role = "USER" if h.get("role") == "user" else "CHATBOT"
            co_history.append({"role": role, "message": h.get("message", "")})

    # Auto-detection of working model
    for model_name in MODEL_CANDIDATES:
        try:
            print(f"[Sage] Probing Cohere model: {model_name}")
            response = client.chat(
                model=model_name,
                message=user_query,
                preamble=SYSTEM_PROMPT,
                chat_history=co_history,
                temperature=0.3
            )
            if response and hasattr(response, 'text'):
                print(f"[Sage] SUCCESS with model: {model_name}")
                return response.text.strip()
        except Exception as e:
            print(f"[Sage] Model {model_name} failed: {e}")
            continue

    return _fallback_response(user_query)

def _fallback_response(query: str) -> str:
    # (Same professional fallback)
    return ("I am listening with absolute care 🌿. Your words matter, and I want to understand exactly what you're experiencing. "
            "Could you tell me a little bit more about what's been most difficult for you today?")

def clear_session(sid): pass