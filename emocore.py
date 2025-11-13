def detect_emotion(text):
    text = text.lower()
    emotions = {
        "sad": ["sad", "down", "unhappy", "bad", "cry"],
        "happy": ["happy", "good", "great", "nice"],
        "angry": ["angry", "mad", "furious", "annoyed"],
        "anxious": ["worried", "scared", "nervous", "anxious"],
    }

    for emotion, words in emotions.items():
        for w in words:
            if w in text:
                return emotion
    return "neutral"


def respond(emotion):
    responses = {
        "sad": "I’m really sorry you're feeling sad. Want to talk about what’s bothering you?",
        "angry": "It’s okay to feel angry. Let’s take a deep breath together.",
        "happy": "That's wonderful to hear! What's making you happy today?",
        "anxious": "That sounds stressful. Let’s try a quick grounding exercise: name 3 things you can see.",
        "neutral": "I’m listening — tell me more.",
    }
    return responses.get(emotion, "I'm here for you.")