from flask import Flask, render_template, request, jsonify
from emocore import detect_emotion, respond

app = Flask(_name_)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    user_text = request.json["text"]
    emotion = detect_emotion(user_text)
    bot_reply = respond(emotion)
    return jsonify({"emotion": emotion, "reply": bot_reply})

if _name_ == "_main_":
    app.run(debug=True)