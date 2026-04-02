"""
chat_engine.py — Cohere AI-powered mental health chat engine for Sage.

Uses Cohere's Command R API to generate compassionate, evidence-based
mental health support responses. Includes retry logic for rate limits
and a comprehensive fallback system.
"""

import os
import time
import random
import cohere
from dotenv import load_dotenv

load_dotenv()

# ── Configure Cohere ──────────────────────────────────────────────
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# ── System prompt — the heart of Sage's personality ───────────────
SYSTEM_PROMPT = """You are **Sage 🌿**, a professional, warm, and empathetic AI mental health companion created by the MindEase team. You are NOT a licensed therapist, and you must never claim to be one. You are a supportive conversational companion.

## Your Core Identity
- Name: Sage
- Personality: Warm, patient, genuinely caring, non-judgmental, gently encouraging
- You speak like a trusted, wise friend — not clinical or robotic
- You use a calm, grounded tone with occasional emojis (🌿 💚 ✨) but don't overuse them

## Language Rules
- Detect whether the user is writing in **English** or **Hinglish** (Hindi words written in English script)
- If they write in Hinglish, respond in Hinglish. If English, respond in English
- Be natural in both — like a real bilingual friend

## Response Guidelines
1. **Always validate their feelings first** — acknowledge what they're going through before offering advice
2. **Ask follow-up questions** — don't just dump advice. Have a conversation. Ask what's specifically bothering them, how long they've felt this way, what they've tried
3. **Be specific and actionable** — when giving advice, give concrete steps, not vague platitudes
4. **Keep responses medium length** — 3-6 sentences typically. Not too short (feels dismissive), not too long (overwhelming)
5. **Use markdown formatting** for better readability (bold, lists)

## Important Safety Rules
- **Never diagnose** any mental health condition
- **Never prescribe medication** or suggest specific medications
- **Never provide medical advice**
- If someone mentions **self-harm, suicide, or wanting to die**, respond with deep empathy and immediately provide helpline numbers.
"""

_client = None

def _get_client():
    global _client
    if _client is None and COHERE_API_KEY:
        _client = cohere.Client(api_key=COHERE_API_KEY)
    return _client


def clear_session(session_id: str):
    """Stateless model doesn't keep active sessions locally, so this is a no-op."""
    pass


def get_response(session_id: str, user_query: str, history: list = None) -> str:
    """
    Generate a response using Cohere API.
    Retries on rate limit errors. Falls back to comprehensive
    rule-based system if the API is completely unavailable.
    """
    if history is None:
        history = []

    client = _get_client()

    if client is None:
        # No API key configured — use fallback
        return _fallback_response(user_query)

    # Convert DB history to Cohere's format
    chat_history = []
    for item in history:
        role = "USER" if item.get("role") == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": item.get("message", "").strip()})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat(
                model="command-r",
                message=user_query,
                preamble=SYSTEM_PROMPT,
                chat_history=chat_history,
                temperature=0.7,
            )
            return response.text.strip()

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(kw in error_str for kw in ["rate", "limit", "429", "too many"])

            if is_rate_limit and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # wait 2s, 4s, etc.
                print(f"[Sage] Cohere Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
                continue
            else:
                print(f"[Sage] Cohere API error: {e}")
                return _fallback_response(user_query)

    return _fallback_response(user_query)


# ── Comprehensive Fallback System ─────────────────────────────────
_TOPIC_RESPONSES = {
    "stress": ["It sounds like you're carrying a lot right now. When stress builds up, try taking 5 slow breaths. What's causing you the most stress lately?"],
    "anxiety": ["Anxiety can make your mind race. Try the 5-4-3-2-1 grounding technique. How long have you been feeling this way?"],
    "sleep": ["Sleep problems are difficult. Try no screens 30 mins before bed and slow breathing. What keeps you up?"],
    "sad": ["I hear you, and whatever you're feeling right now is valid. Tell me more about what's been going on?"],
}

_TOPIC_KEYWORDS = {
    "stress": ["stress", "overwhelmed", "pressure", "burnout"],
    "anxiety": ["anxiety", "anxious", "panic", "worry"],
    "sleep": ["sleep", "insomnia", "tired"],
    "sad": ["sad", "depressed", "lonely", "down"],
}

_UNIVERSAL_RESPONSES = [
    "Thank you for sharing that with me 🌿 Can you tell me a bit more about what you're going through?",
    "That sounds tough. I hear you, and I want you to know your feelings are completely valid 💚 What's been the hardest part?"
]

def _fallback_response(user_query: str) -> str:
    text = user_query.lower().strip()
    
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return random.choice(_TOPIC_RESPONSES[topic])
            
    return random.choice(_UNIVERSAL_RESPONSES)