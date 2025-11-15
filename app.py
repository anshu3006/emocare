from flask import Flask, render_template, request, jsonify
from emocore import detect_emotion, generate_reply, openai_reply_available, use_openai_reply
import sqlite3
import time
import os

# Simple conversation store using SQLite (keeps last N messages per session)
DB_FILE = "chat_history.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        text TEXT,
        emotion TEXT,
        ts REAL
    )
    """
    )
    conn.commit()
    conn.close()

app = Flask(__name__)


def save_message(session_id: str, role: str, text: str, emotion: str = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (session_id, role, text, emotion, ts) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, text, emotion, time.time()),
    )
    conn.commit()
    conn.close()


def load_history(session_id: str, limit: int = 50):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT role, text, emotion, ts FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    rows = c.fetchall()
    conn.close()
    # return as list of dicts in chronological order
    out = []
    for r in reversed(rows):
        out.append({"from": r[0], "text": r[1], "emotion": r[2], "ts": r[3]})
    return out


@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/chat")
def chat_page():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400

    session_id = data.get("session_id", "default_session")
    # 1) detect emotion
    emotion, scores = detect_emotion(text)
    # 2) save user message
    save_message(session_id, "user", text, emotion)
    # 3) load short history
    history = load_history(session_id, limit=20)
    # 4) generate reply (prefer OpenAI if key set)
    if openai_reply_available():
        reply = use_openai_reply(text, emotion, history)
    else:
        reply = generate_reply(text, emotion, history)
    # 5) save bot reply
    save_message(session_id, "assistant", reply, emotion)
    # 6) return structured response
    return jsonify(
        {
            "emotion": emotion,
            "scores": scores,
            "reply": reply,
            "history": history[-12:],  # recent history
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
