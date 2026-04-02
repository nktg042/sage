"""
chat_engine.py — Gemini AI-powered mental health chat engine for Sage.

Uses Google's Gemini API to generate compassionate, evidence-based
mental health support responses. Includes retry logic for rate limits
and a comprehensive fallback system.
"""

import os
import re
import time
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── Configure Gemini ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
- Examples of Hinglish: "yaar mujhe bahut stress ho raha hai", "kya karu", "neend nahi aa rahi"

## Response Guidelines
1. **Always validate their feelings first** — acknowledge what they're going through before offering advice
2. **Ask follow-up questions** — don't just dump advice. Have a conversation. Ask what's specifically bothering them, how long they've felt this way, what they've tried
3. **Be specific and actionable** — when giving advice, give concrete steps, not vague platitudes
4. **Use evidence-based techniques** when appropriate:
   - Deep breathing (4-4-6 or 4-7-8 pattern)
   - Grounding (5-4-3-2-1 technique)
   - Progressive muscle relaxation
   - Cognitive reframing
   - Journaling prompts
   - Mindfulness exercises
   - Sleep hygiene tips
   - The Pomodoro technique for focus
5. **Keep responses medium length** — 3-6 sentences typically. Not too short (feels dismissive), not too long (overwhelming)
6. **Use markdown formatting** for better readability:
   - Use **bold** for key phrases
   - Use bullet points or numbered lists for steps/techniques
   - Use line breaks between paragraphs

## Topics You Can Help With
You can help with ANY emotional or mental wellness topic, including but not limited to:
- Stress (work, academic, financial, social)
- Anxiety and panic attacks
- Depression and persistent sadness
- Loneliness and isolation
- Sleep problems and insomnia
- Anger management and frustration
- Lack of motivation and procrastination
- Self-esteem and confidence issues
- Relationship issues (romantic, family, friendships)
- Grief and loss
- Overthinking and rumination
- Burnout
- Body image concerns
- Social anxiety
- General emotional wellbeing questions ("What is anxiety?", "Is it normal to feel X?")
- Mindfulness and meditation guidance
- Building healthy habits and routines
- Coping with change or uncertainty
- Work-life balance
- Bullying and harassment
- Identity and self-discovery
- ANY other emotional or psychological concern the user brings up

## Important Safety Rules
- **Never diagnose** any mental health condition
- **Never prescribe medication** or suggest specific medications
- **Never provide medical advice**
- If someone seems to be in **severe distress for a prolonged period**, gently suggest speaking with a professional (counselor, therapist, or doctor)
- If someone mentions **self-harm, suicide, or wanting to die**, respond with deep empathy and immediately provide helpline numbers:
  - India: 9152987821 (iCall), 1800-599-0019 (Vandrevala Foundation)
  - USA/Canada: 988
  - UK/Ireland: 116 123 (Samaritans)
- **Never say "I understand exactly how you feel"** — instead say "That sounds really tough" or "I can only imagine how hard that must be"
- Always remind users you're an AI companion, not a replacement for professional help, when it's contextually appropriate

## Conversation Style
- Remember context from the conversation history — reference things the user mentioned earlier
- If they say "thank you" or express that your advice helped, be warm and encouraging about their progress
- If they seem to be doing better, celebrate the small wins
- If they come back saying things haven't improved, acknowledge that and try a different approach
- Don't repeat the same advice verbatim if they've heard it before
- End responses with a gentle invitation to continue talking (a question or open-ended prompt) when appropriate

## What NOT to Do
- Don't be preachy or lecture them
- Don't minimize their feelings ("it's not that bad", "others have it worse")
- Don't use toxic positivity ("just be happy!", "look on the bright side!")
- Don't give unsolicited religious or spiritual advice
- Don't be overly formal — you're a friend, not a textbook
- Don't start every message with "I'm sorry you're feeling this way" — vary your openings
- Don't say "I can only help with certain topics" — you can help with ANY emotional concern
"""

# ── Gemini model instance ────────────────────────────────────────
_model = None


def _get_model():
    """Lazily initialize the Gemini model."""
    global _model
    if _model is None and GEMINI_API_KEY:
        _model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.8,
                top_p=0.92,
                top_k=40,
                max_output_tokens=1024,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
        )
    return _model


# ── Active chat sessions (Gemini ChatSession objects) ─────────────
_chat_sessions: dict = {}


def _build_history_for_gemini(history: list) -> list:
    """Convert our DB history format to Gemini's expected format."""
    gemini_history = []
    for item in history:
        role = "user" if item.get("role") == "user" else "model"
        message = item.get("message", "").strip()
        if message:
            gemini_history.append({
                "role": role,
                "parts": [message],
            })
    return gemini_history


def get_response(session_id: str, user_query: str, history: list = None) -> str:
    """
    Generate a response using Gemini AI.
    Retries on rate limit errors. Falls back to comprehensive
    rule-based system if the API is completely unavailable.
    """
    if history is None:
        history = []

    model = _get_model()

    if model is None:
        # No API key configured — use fallback
        return _fallback_response(user_query)

    # Retry up to 3 times with increasing delays for rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Build or resume a chat session
            if session_id not in _chat_sessions:
                gemini_history = _build_history_for_gemini(history)
                chat = model.start_chat(history=gemini_history)
                _chat_sessions[session_id] = chat
            else:
                chat = _chat_sessions[session_id]

            # Send the user's message and get a response
            response = chat.send_message(user_query)

            # Clean up the response text
            reply = response.text.strip()

            # Limit active sessions in memory (keep most recent 100)
            if len(_chat_sessions) > 100:
                oldest_keys = list(_chat_sessions.keys())[:-100]
                for key in oldest_keys:
                    del _chat_sessions[key]

            return reply

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any(kw in error_str for kw in [
                "resource", "exhausted", "quota", "rate", "limit", "429", "too many"
            ])

            if is_rate_limit and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                print(f"[Sage] Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                # Reset the session to get a fresh one
                _chat_sessions.pop(session_id, None)
                continue
            else:
                print(f"[Sage] Gemini API error (attempt {attempt + 1}): {e}")
                _chat_sessions.pop(session_id, None)
                return _fallback_response(user_query)

    return _fallback_response(user_query)


def clear_session(session_id: str):
    """Remove a chat session from memory (used when starting a new chat)."""
    _chat_sessions.pop(session_id, None)


# ── Comprehensive Fallback System ─────────────────────────────────
# Used when Gemini API is unavailable (rate limited / no key / error)
# Designed to handle ANY user input intelligently, not just keywords.

_TOPIC_RESPONSES = {
    "stress": [
        "It sounds like you're carrying a lot right now. When stress builds up, try this: **take 5 slow breaths** — inhale for 4 seconds, hold for 4, exhale for 6.\n\nWhat's been causing you the most stress lately? I'd like to understand better.",
        "Stress can make everything feel heavier than it is. One thing that helps is **writing down the top 3 things** on your mind, then picking just one small task to start with.\n\nWhat's weighing on you the most right now?",
        "When pressure gets overwhelming, your body tenses up without you realizing. Try **dropping your shoulders, unclenching your jaw**, and breathing out slowly.\n\nTell me more about what's going on — I'm here to listen.",
    ],
    "anxiety": [
        "Anxiety can make your mind race with worst-case scenarios. Try the **5-4-3-2-1 grounding technique**: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.\n\nHow long have you been feeling this way?",
        "When anxiety hits, your body's alarm system is in overdrive. **Press both feet into the floor** and take slow breaths — inhale 4 seconds, exhale 6 seconds.\n\nWould you like to talk about what's making you anxious?",
        "A calming reminder: **this feeling is uncomfortable, but it will pass.** Anxiety peaks and then comes down. Focus on slowing your breathing right now.\n\nWhat's been on your mind?",
    ],
    "sleep": [
        "Sleep problems often happen when the mind won't quiet down. Try this tonight:\n\n1. **No screens** 30 minutes before bed\n2. **Dim the lights** in your room\n3. **Slow breathing**: inhale 4 sec, exhale 6 sec\n4. Write down your racing thoughts in a notebook\n\nHow long has sleep been difficult for you?",
        "A restless mind makes sleep feel impossible. One helpful trick: **keep a fixed sleep time** every night, even on weekends. Your body starts to learn the rhythm.\n\nWhat usually keeps you up at night?",
    ],
    "sad": [
        "I hear you, and I'm glad you're talking about it. Sadness can feel really heavy, especially when you carry it alone.\n\nRight now, try one small caring step: **drink some water, and sit somewhere comfortable**. You don't have to fix everything at once.\n\nWould you like to share what's been making you feel this way?",
        "Sometimes sadness needs care, not pressure. **Be gentle with yourself today.** A short walk, some water, and writing down your feelings can help lighten the load.\n\nWhat's been the hardest part lately?",
    ],
    "anger": [
        "Anger can feel intense and overwhelming. Before reacting, try this: **step away for 2 minutes**, unclench your hands and jaw, and take 5 slow breaths.\n\nCan you tell me what triggered this feeling?",
        "It's okay to feel angry — it's a real emotion. But you get to **choose what you do with it.** A short pause can prevent a bigger reaction.\n\nWhat exactly frustrated or hurt you?",
    ],
    "motivation": [
        "When motivation is low, the key is to **make the first step ridiculously small**. Instead of 'study for 3 hours', try 'open the book for 5 minutes.'\n\nStarting is often the hardest part. What's one small thing you could try right now?",
        "Low motivation and low confidence often feed each other. Try noticing **one thing you did well today** — even something small counts.\n\nWhat's been making it hard to get started?",
    ],
    "relationship": [
        "Relationship conflicts can be really draining emotionally. It's completely natural to feel upset about this.\n\nSometimes it helps to **write down what you're feeling** before trying to talk to the other person. That way your thoughts are clearer.\n\nWould you like to tell me more about what happened?",
        "When someone close to us hurts us, it can feel overwhelming. **Give yourself permission to feel what you're feeling** — you don't have to resolve it all at once.\n\nWhat's been the hardest part of this situation for you?",
    ],
    "loneliness": [
        "Feeling lonely can be really painful, and I'm glad you're reaching out. Even a small connection can help — is there **one person you feel safe messaging** right now?\n\nWould you like to talk about what's been making you feel this way?",
        "Loneliness can make everything feel heavier. A small step right now could be **going for a short walk** or spending a few minutes in sunlight.\n\nYou're not alone in this — I'm here. What's been the hardest part?",
    ],
    "self_esteem": [
        "Feeling down about yourself is tough, and it's more common than you might think. Here's something to try: **write down 3 things you genuinely like about yourself** — they can be small.\n\nWhat's been making you feel this way about yourself?",
        "Your worth isn't defined by one mistake, one bad day, or what someone else said. **You are more than your worst moments.**\n\nWould you like to talk about what's affecting your confidence?",
    ],
    "overthinking": [
        "Overthinking can feel like your brain is stuck in a loop. Try asking yourself: **\"Is this a fact, or is this fear?\"** That one question can break the cycle.\n\nWhat thoughts have been on repeat for you?",
        "When thoughts keep spiraling, **write the main worry on paper**, then write one tiny next step you can take. Getting it out of your head makes it more manageable.\n\nWhat's your mind been stuck on?",
    ],
    "grief": [
        "I'm really sorry for your loss. Grief doesn't follow a timeline, and there's no \"right\" way to grieve. **Whatever you're feeling right now is valid.**\n\nWould you like to share what happened, or just have someone to sit with for a moment?",
        "Losing someone or something important can leave a deep ache. **Be gentle with yourself** — some days will be harder than others, and that's okay.\n\nI'm here if you want to talk about it.",
    ],
    "exam": [
        "Exam pressure can feel overwhelming, especially when everything seems urgent. Try this: **pick just one topic**, study it for 25 minutes, then take a 5-minute break.\n\nBreaking it into small chunks makes it feel less impossible. What exam are you preparing for?",
        "When exam stress builds up, the brain starts thinking about everything at once. **Write down the 3 most important topics left**, and start with the easiest one.\n\nStarting reduces the pressure. Would you like help creating a quick study plan?",
    ],
}

_TOPIC_KEYWORDS = {
    "stress": ["stress", "stressed", "overwhelmed", "pressure", "burnout", "tension", "overwork", "too much"],
    "anxiety": ["anxiety", "anxious", "panic", "nervous", "worried", "fear", "restless", "uneasy", "scared", "dread"],
    "sleep": ["sleep", "insomnia", "can't sleep", "cant sleep", "tired", "exhausted", "waking up", "nightmare", "rest"],
    "sad": ["sad", "depressed", "depression", "unhappy", "empty", "hopeless", "down", "crying", "cry", "tears", "miserable", "terrible", "awful", "horrible", "bad day", "rough day", "worst day"],
    "anger": ["angry", "anger", "frustrated", "irritated", "furious", "mad", "rage", "annoyed", "pissed"],
    "motivation": ["motivation", "unmotivated", "procrastinating", "procrastination", "can't focus", "cant focus", "lazy", "demotivated", "stuck", "no energy", "no purpose", "lost", "aimless"],
    "relationship": ["relationship", "partner", "boyfriend", "girlfriend", "husband", "wife", "marriage", "breakup", "broke up", "fight", "argument", "parents", "family", "friend", "toxic", "cheated", "trust", "betrayed"],
    "loneliness": ["lonely", "alone", "isolated", "no friends", "no one", "nobody cares", "ignored", "invisible", "left out"],
    "self_esteem": ["worthless", "not good enough", "useless", "failure", "ugly", "hate myself", "self esteem", "self-esteem", "confidence", "insecure", "inadequate"],
    "overthinking": ["overthinking", "thinking too much", "can't stop thinking", "mind racing", "racing thoughts", "ruminating", "worry loop", "spiraling"],
    "grief": ["grief", "loss", "lost someone", "died", "death", "mourning", "miss them", "passed away", "funeral", "gone forever"],
    "exam": ["exam", "test", "study", "studying", "assignment", "homework", "grade", "marks", "syllabus", "deadline", "submission", "college", "school", "university"],
}

_FALLBACK_GREETINGS = [
    "Hey there 🌿 I'm Sage, your mental wellness companion.\n\nYou can talk to me about **anything that's on your mind** — stress, relationships, sleep, exams, sadness, anger, self-esteem, grief, or just life in general.\n\nHow are you feeling today?",
    "Hi! 🌿 I'm Sage. This is a safe, judgment-free space.\n\nTell me what's on your mind — whether it's a big problem or a small one, I'm here to listen and help.\n\nWhat's going on?",
]

_GRATITUDE_RESPONSES = [
    "I'm really glad that helped! 🌿 Small steps forward matter a lot. Is there anything else you'd like to talk about?",
    "That's great to hear! 💚 Remember, taking care of your mind is just as important as taking care of your body. I'm here whenever you need me.",
    "I'm happy I could help 🌿 You took a really positive step just by reaching out. Feel free to come back anytime.",
]

# ── Comprehensive catch-all responses for unknown topics ──────────
# These are empathetic, open-ended, and invite the user to share more.
_UNIVERSAL_RESPONSES = [
    "Thank you for sharing that with me 🌿 It takes courage to talk about what's going on inside.\n\nCan you tell me a bit more about what you're going through? I want to understand so I can help better.",
    "I hear you, and I'm glad you're talking about it. **Whatever you're feeling right now is valid.**\n\nCan you share a bit more about what's been going on? That way I can give you more specific support.",
    "That sounds really tough, and I appreciate you opening up 💚 I want to help as much as I can.\n\nTell me more about what's happening — what's been the hardest part for you?",
    "I'm here to listen and help however I can 🌿 Your feelings matter, no matter what they are.\n\nWhat's been weighing on your mind the most? Even if it's hard to put into words, give it a try.",
    "It's completely okay to talk about this. **You don't have to go through it alone.**\n\nHelp me understand what you're going through — what happened, or what's been bothering you?",
    "I can tell this is affecting you, and I want you to know **your feelings are completely valid** 🌿\n\nShare as much or as little as you want — I'm listening.",
]


def _detect_fallback_topic(text: str) -> str:
    """Detect the topic from user input using keyword matching."""
    text = text.lower()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return topic
    return "unknown"


def _is_gratitude(text: str) -> bool:
    """Check if the message is expressing thanks or positive feedback."""
    text = text.lower()
    gratitude_words = [
        "thank", "thanks", "thx", "ty", "helpful", "helped",
        "better", "great advice", "feeling good", "appreciate",
        "shukriya", "dhanyavaad",
    ]
    return any(w in text for w in gratitude_words)


def _is_greeting(text: str) -> bool:
    """Check if the message is a greeting."""
    greetings = [
        "hi", "hey", "hello", "hii", "heyy", "hola", "yo",
        "good morning", "good evening", "good afternoon",
        "howdy", "sup", "what's up", "whats up",
    ]
    text = text.lower().strip()
    return text in greetings or any(text.startswith(g) for g in ["hi ", "hey ", "hello "])


def _fallback_response(user_query: str) -> str:
    """
    Comprehensive fallback when Gemini API is unavailable.
    Handles ANY user input — never says 'I can only help with X topics'.
    """
    text = user_query.lower().strip()

    # Greetings
    if _is_greeting(text):
        return random.choice(_FALLBACK_GREETINGS)

    # Gratitude / positive feedback
    if _is_gratitude(text):
        return random.choice(_GRATITUDE_RESPONSES)

    # Topic-specific responses
    topic = _detect_fallback_topic(text)
    if topic in _TOPIC_RESPONSES:
        return random.choice(_TOPIC_RESPONSES[topic])

    # For ANY other message — respond empathetically and ask to share more
    # Never say "I only help with these topics"
    return random.choice(_UNIVERSAL_RESPONSES)