"""
emocore.py
- detect_emotion(text): returns emotion label + scores
- generate_reply(text, emotion, history): returns an empathetic reply
- optional: use_openai_reply(text, emotion, history) if OPENAI_API_KEY is set (not required)
"""

from typing import Tuple, Dict, List
import os

# Try to import transformers; if not available, user will install per instructions.
try:
    from transformers import pipeline
except Exception:
    pipeline = None

# Supported emotion labels (model dependent)
DEFAULT_EMOTIONS = ["sadness", "joy", "love", "anger", "fear", "surprise", "neutral"]

# Load classifier lazily
_CLASSIFIER = None
_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"  # small, good general model


def _load_classifier():
    global _CLASSIFIER
    if _CLASSIFIER is None:
        if pipeline is None:
            raise RuntimeError(
                "transformers not installed. Run: pip install transformers[torch] torch"
            )
        # create a text-classification pipeline
        _CLASSIFIER = pipeline("text-classification", model=_MODEL_NAME, return_all_scores=True)
    return _CLASSIFIER


def detect_emotion(text: str) -> Tuple[str, Dict[str, float]]:
    """
    Returns (top_emotion_label, scores_dict)
    scores_dict maps label->score (0..1)
    """
    text = (text or "").strip()
    if not text:
        return "neutral", {e: 0.0 for e in DEFAULT_EMOTIONS}

    try:
        clf = _load_classifier()
        results = clf(text[:512])  # limit length
        # results is a list of dicts with 'label' and 'score'
        # Some pipelines return list-of-lists (for return_all_scores=True)
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
            scores_list = results[0]
        else:
            scores_list = results

        scores = {item["label"].lower(): float(item["score"]) for item in scores_list}
        # normalize to include our default emotions if missing
        for e in DEFAULT_EMOTIONS:
            scores.setdefault(e, 0.0)
        # pick top
        top = max(scores.items(), key=lambda kv: kv[1])[0]
        # Map some labels to simpler categories (optional)
        mapped = _map_label(top)
        return mapped, scores
    except Exception as e:
        # If model fails, fall back to simple keyword detector
        return _simple_keyword_detect(text), {e: 0.0 for e in DEFAULT_EMOTIONS}


def _map_label(label: str) -> str:
    """
    Map model labels to simplified set: sad, happy, angry, anxious, neutral, surprise, love
    """
    l = label.lower()
    if "sad" in l or "sadness" in l:
        return "sad"
    if "joy" in l or "happy" in l or "happiness" in l:
        return "happy"
    if "anger" in l or "angry" in l:
        return "angry"
    if "fear" in l or "anxious" in l or "anxiety" in l or "panic" in l:
        return "anxious"
    if "love" in l:
        return "love"
    if "surprise" in l:
        return "surprised"
    return "neutral"


def _simple_keyword_detect(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["sad", "unhappy", "depressed", "cry", "lonely"]):
        return "sad"
    if any(w in t for w in ["happy", "glad", "awesome", "great", "joy"]):
        return "happy"
    if any(w in t for w in ["angry", "mad", "furious", "annoyed", "hate"]):
        return "angry"
    if any(w in t for w in ["anxious", "scared", "nervous", "worried", "panic"]):
        return "anxious"
    if any(w in t for w in ["love", "luv"]):
        return "love"
    return "neutral"


# --- Empathetic reply generator (template-based, robust and safe) --- #

# Short helpers to craft replies:
_VALIDATION = {
    "sad": [
        "I'm really sorry you're going through this. That sounds really heavy.",
        "That must be so difficult—thank you for sharing that with me."
    ],
    "angry": [
        "I can hear the anger in your words. It's valid to feel upset.",
        "Anger is a natural reaction. I'm here to listen without judgement."
    ],
    "anxious": [
        "Being anxious feels overwhelming—you're not alone in that.",
        "I hear that worry. Let's try something grounding together if you're open to it."
    ],
    "happy": [
        "That's wonderful to hear—thank you for sharing your joy!",
        "I'm so glad you're feeling good. What made you feel this way?"
    ],
    "love": [
        "That's lovely — feeling connected is so meaningful.",
        "I'm happy you have something or someone bringing you warmth."
    ],
    "surprised": [
        "Oh—that sounds surprising. Want to tell me more?",
        "That must have been unexpected. How are you processing it?"
    ],
    "neutral": [
        "I'm here and listening—tell me more if you'd like.",
        "Thanks for sharing. What else is on your mind?"
    ],
}

# Practical suggestions mapped by emotion
_SUGGESTIONS = {
    "sad": [
        "Would you like a quick breathing exercise? Or would you like to tell me more about what happened?",
        "Sometimes writing one sentence about what you feel can help. Want to try?"
    ],
    "angry": [
        "A slow 4-4-4 breathing can help calm: breathe in 4s, hold 4s, out 4s. Want to try?",
        "If it helps, you can name one thing you can change about the situation and one you can't."
    ],
    "anxious": [
        "Try grounding: name 5 things you can see, 4 you can touch, 3 you can hear.",
        "Shallow breathing makes anxiety worse—slow deep breaths often help."
    ],
    "happy": [
        "Would you like me to save this as a happy memory in your journal?",
        "Want to celebrate? I can share a short compliment or a motivating quote."
    ],
    "love": [
        "That's heartwarming. Would you like to reflect on what made this connection strong?",
        "Would you like to note this as a positive memory?"
    ],
    "surprised": [
        "Do you want to unpack what surprised you and how you feel about it?",
        "If it's good surprise—congratulations! If it's not, I'm here to listen."
    ],
    "neutral": [
        "Would you like a prompt to help share more—like 'What happened today?'",
        "We can try a short check-in exercise if you'd like."
    ],
}


def generate_reply(user_text: str, emotion: str, history: List[Dict] = None) -> str:
    """
    Create a compassionate reply combining validation, reflection and an optional suggestion.
    history is a list of prior messages (not required).
    """
    if history is None:
        history = []

    # Choose a validation sentence
    val_candidates = _VALIDATION.get(emotion, _VALIDATION["neutral"])
    sug_candidates = _SUGGESTIONS.get(emotion, _SUGGESTIONS["neutral"])

    import random

    val = random.choice(val_candidates)
    sug = random.choice(sug_candidates)

    # Reflection: echo a short part of their message (first 10-12 words)
    words = user_text.strip().split()
    reflection = ""
    if len(words) > 0:
        reflection = "You said: \"" + " ".join(words[:12]) + ("...\"" if len(words) > 12 else "\"")

    # Build reply carefully — avoid making medical claims.
    parts = [val]
    if reflection:
        parts.append(reflection)
    parts.append(sug)
    reply = " ".join(parts)

    return reply


# Optional: If user has OPENAI_API_KEY, we can generate richer reply via GPT.
# This is optional and disabled by default.
def openai_reply_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def use_openai_reply(user_text: str, emotion: str, history: List[Dict] = None) -> str:
    """
    If you set environment OPENAI_API_KEY, this function calls OpenAI to generate a
    more natural and flexible empathetic reply. Not required for the hackathon.
    """
    try:
        import openai

        openai.api_key = os.environ.get("OPENAI_API_KEY")
        context = "You are an empathetic assistant that validates feelings, reflects briefly, and offers a small coping suggestion. Be concise and kind."
        messages = [{"role": "system", "content": context}]
        # include a short history if available
        if history:
            for turn in history[-6:]:
                role = "user" if turn.get("from") == "user" else "assistant"
                messages.append({"role": role, "content": turn.get("text", "")})
        # finally the user text
        messages.append({"role": "user", "content": f"{user_text}\n\nDetected emotion: {emotion}"})
        resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=messages, max_tokens=150, temperature=0.7)
        return resp["choices"][0]["message"]["content"].strip()
    except Exception:
        # fallback
        return generate_reply(user_text, emotion, history)
