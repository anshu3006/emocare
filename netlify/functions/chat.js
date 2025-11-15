exports.handler = async function(event) {
  try {
    const data = JSON.parse(event.body || '{}');
    const text = String(data.text || '').trim();
    const sessionId = String(data.session_id || 'default_session');
    if (!text) {
      return { statusCode: 400, body: JSON.stringify({ error: 'No text provided.' }) };
    }

    function detectEmotion(t) {
      const s = t.toLowerCase();
      if (['sad','unhappy','depressed','cry','lonely'].some(w => s.includes(w))) return 'sad';
      if (['happy','glad','awesome','great','joy'].some(w => s.includes(w))) return 'happy';
      if (['angry','mad','furious','annoyed','hate'].some(w => s.includes(w))) return 'angry';
      if (['anxious','scared','nervous','worried','panic'].some(w => s.includes(w))) return 'anxious';
      if (['love','luv'].some(w => s.includes(w))) return 'love';
      if (['surprise','surprised','shocked'].some(w => s.includes(w))) return 'surprised';
      return 'neutral';
    }

    const VALIDATION = {
      sad: ["I'm really sorry you're going through this.", "That must be so difficult—thank you for sharing."],
      angry: ["I can hear the anger in your words.", "Anger is a natural reaction."],
      anxious: ["Being anxious feels overwhelming—you're not alone.", "I hear that worry. Let's try something grounding."],
      happy: ["That's wonderful to hear!", "I'm glad you're feeling good."],
      love: ["That's lovely—feeling connected is meaningful.", "Happy you have warmth in your life."],
      surprised: ["That sounds surprising.", "That must have been unexpected."],
      neutral: ["I'm here and listening.", "Thanks for sharing."]
    };

    const SUGGESTIONS = {
      sad: ["Would you like a quick breathing exercise?", "Sometimes writing one sentence about what you feel can help."],
      angry: ["Try slow 4-4-4 breathing.", "Name one thing you can change and one you can't."],
      anxious: ["Try grounding: 5 things you see, 4 touch, 3 hear.", "Slow deep breaths can help."],
      happy: ["Want to save this as a happy memory?", "Want to celebrate with a compliment?"],
      love: ["Would you like to reflect on what made this connection strong?", "Note this as a positive memory?"],
      surprised: ["Do you want to unpack what surprised you?", "If it's good—congrats! If not, I'm here."],
      neutral: ["Would you like a prompt—like 'What happened today?'", "We can try a short check-in exercise."]
    };

    function generateReply(userText, emotion) {
      const v = (VALIDATION[emotion] || VALIDATION.neutral);
      const s = (SUGGESTIONS[emotion] || SUGGESTIONS.neutral);
      const val = v[Math.floor(Math.random() * v.length)];
      const sug = s[Math.floor(Math.random() * s.length)];
      const words = userText.trim().split(/\s+/);
      const reflection = words.length ? `You said: "${words.slice(0, 12).join(' ')}${words.length > 12 ? '...' : ''}"` : '';
      return [val, reflection, sug].filter(Boolean).join(' ');
    }

    const emotion = detectEmotion(text);
    const reply = generateReply(text, emotion);

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ emotion, scores: {}, reply, history: [] })
    };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ error: 'Server error.' }) };
  }
};