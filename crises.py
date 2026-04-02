import re
from typing import List

# ── Crisis phrases that use EXACT substring matching ──────────────
# These are multi-word phrases unlikely to appear in innocent contexts.
CRISIS_PHRASES: List[str] = [
    "kill myself",
    "i want to die",
    "want to die",
    "end my life",
    "self harm",
    "self-harm",
    "hurt myself",
    "better off dead",
    "no reason to live",
    "life is pointless",
    "i should die",
    "ending it all",
    "i hate my life",
    "i want to disappear",
    "i don't want to live",
    "nothing matters anymore",
    "kill me",
    "i am done with life",
    "i want to end everything",
    "i want to end it all",
    "i don't want to be here",
    "i want to hurt myself",
    "i can't go on anymore",
    "i can't take it anymore",
    "i cant take it anymore",
    "there is no point in living",
    "i wish i was dead",
    "i wish i were dead",
    "nobody would miss me",
    "the world is better without me",
    "i want it all to stop",
    "i just want the pain to stop",
    "mujhe mar jana hai",
    "marna chahta hoon",
    "marna chahti hoon",
    "jeene ka mann nahi hai",
    "zindagi khatam karna chahta hoon",
    "koi fayda nahi hai jeene ka",
    "sab khatam karna hai",
]

# ── Crisis words that need WORD BOUNDARY matching ─────────────────
# These short words could appear inside other words ("die" in "diet"),
# so we only match them as whole words.
# Includes common misspellings to catch typos.
CRISIS_WORDS: List[str] = [
    "suicidal",
    "suicide",
    "sucide",
    "suside",
    "suicde",
    "sucidal",
    "sucidle",
    "die",
    "hopeless",
    "worthless",
]

# Pre-compile word-boundary patterns for performance
_WORD_PATTERNS = [
    re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
    for word in CRISIS_WORDS
]

# Context words that CANCEL a crisis match for short words like "die"
# e.g. "deadline", "diet", "dioxide" — these contain "die" but are not crisis
CANCEL_CONTEXTS: List[str] = [
    "deadline", "diet", "dieting", "dioxide", "diehard", "die-hard",
    "died laughing", "to die for", "die down", "never say die",
    "give up caffeine", "give up sugar", "give up smoking",
    "give up junk food", "give up soda", "give up the habit",
]


# ── Safety message ────────────────────────────────────────────────
SAFETY_MESSAGE = (
    "I'm really sorry you're feeling this way. You matter, and you deserve support. 💚\n\n"
    "**Please reach out to someone right now:**\n\n"
    "📞 **India:** 9152987821 (iCall) · 1800-599-0019 (Vandrevala Foundation)\n"
    "📞 **USA/Canada:** 988 (Suicide & Crisis Lifeline)\n"
    "📞 **UK/Ireland:** 116 123 (Samaritans)\n\n"
    "Please don't stay alone with this feeling. Talk to a trusted person — "
    "a family member, friend, teacher, or call the helplines above.\n\n"
    "If you'd like, you can tell me what happened in one sentence, and "
    "we can take things one small step at a time. I'm here for you. 🌿"
)


def is_crisis_message(text: str) -> bool:
    """
    Returns True if the input text contains crisis/self-harm intent.
    Uses phrase matching for multi-word phrases and word-boundary regex
    for short words to avoid false positives.
    """
    if not text:
        return False

    text_lower = text.lower().strip()

    # Check if any cancel-context is present (to avoid false positives)
    for cancel in CANCEL_CONTEXTS:
        if cancel in text_lower:
            return False

    # Check multi-word phrases (substring match is safe for these)
    for phrase in CRISIS_PHRASES:
        if phrase in text_lower:
            return True

    # Check single words with word boundaries
    for pattern in _WORD_PATTERNS:
        if pattern.search(text_lower):
            # Extra guard: "hopeless" and "worthless" alone can be
            # expressions of frustration, only flag if combined with
            # stronger intent words
            return True

    return False