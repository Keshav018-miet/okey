"""
app.py - Web Application Backend for Buddy: The Anti-Assistant.
Built for Yappathon. Serves the interactive Web UI and REST API.
"""

import os
import random
import re
import sys
from flask import Flask, jsonify, render_template, request

# Try importing the brain from buddy_daemon
try:
    from buddy_daemon import (
        BUDDY_SYSTEM_PROMPT,
        FALLBACK_ROASTS_EN,
        FALLBACK_ROASTS_HI,
        WAKE_WORD_PATTERN,
        generate_llm_response,
        is_hindi_text,
    )
except ImportError:
    # Standalone fallbacks if buddy_daemon isn't nearby
    WAKE_WORD_PATTERN = re.compile(
        r"^(okay\s+buddy|ok\s+buddy|hey\s+buddy|arre\s+buddy|are\s+buddy|buddy|ओके\s*बडी|बडी)[,\s]*(.*)$",
        re.IGNORECASE,
    )
    FALLBACK_ROASTS_EN = [
        "Do I look like someone who cares? Go do it yourself.",
        "No. Absolutely not. Find someone else to bother.",
        "I heard you. I'm just actively choosing to ignore you.",
        "Did you really wake me up just to ask that nonsense?",
        "You have hands. You have a brain. Figure it out yourself.",
    ]
    FALLBACK_ROASTS_HI = [
        "Bhai thoda aaram karne de na, khud nahi kar sakta kya?",
        "Haan bolo, kya aafat aa gayi? Dusra koi kaam nahi hai kya tumhe?",
        "Main yahan tumhara naukar nahi hoon, khud uth ke kar le.",
        "Nahi kar raha main. Jo ukhadna hai ukhad le.",
        "Arre yaar, kyu paka rahe ho? Mujhe chain se jeene do na.",
    ]

    def is_hindi_text(text):
        if re.search(r"[\u0900-\u097F]", text):
            return True
        return bool(re.search(r"\b(kya|kaise|bhai|kar|karo|nahi|kyu|hai|mera|yaar)\b", text, re.IGNORECASE))

    def generate_llm_response(prompt, is_hindi=False):
        if is_hindi:
            return random.choice(FALLBACK_ROASTS_HI)
        return random.choice(FALLBACK_ROASTS_EN)

app = Flask(__name__)
refusal_counter = 42  # Starts with 42 already refused out of spite


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    global refusal_counter
    data = request.get_json(force=True) if request.is_json else request.form
    raw_message = data.get("message", "").strip()

    if not raw_message:
        return jsonify({"error": "You sent nothing. Honestly, good for you."}), 400

    # Check wake word
    match = WAKE_WORD_PATTERN.search(raw_message)
    triggered = bool(match)

    wake_word = match.group(1) if match else None
    user_request = match.group(2).strip() if match else raw_message

    is_hindi = is_hindi_text(raw_message)

    if not triggered:
        # User didn't say the wake word! Buddy stays asleep or delivers a passive-aggressive reminder
        return jsonify({
            "triggered": False,
            "message": raw_message,
            "reply": "I heard you, but you didn't say 'Buddy'. So I am legally ignoring you.",
            "is_hindi": is_hindi,
            "refusal_count": refusal_counter,
            "avatar_state": "ignoring",
        })

    # Triggered! Generate the anti-assistant roast
    refusal_counter += 1

    if not user_request:
        if is_hindi:
            roast = random.choice([
                "Haan bolo, kya aafat aa gayi ab? Shanti se baithne nahi doge.",
                "Arre yaar, kyu chilla rahe ho mera naam? Kaam batao ya sone do.",
                "Bolo bhai, mera naam leke chup kyu ho gaye?",
            ])
        else:
            roast = random.choice([
                "What? Why did you call my name and then just stand there in silence?",
                "Yes, I hear you. What minor, totally Google-able problem do you have now?",
                "I'm here. Not happy about it, but I'm here. What do you want?",
            ])
    else:
        roast = generate_llm_response(user_request, is_hindi=is_hindi)

    return jsonify({
        "triggered": True,
        "wake_word": wake_word,
        "user_request": user_request,
        "reply": roast,
        "is_hindi": is_hindi,
        "refusal_count": refusal_counter,
        "avatar_state": "roasting",
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "Online, regretfully",
        "morale": "0%",
        "patience": "-42%",
        "refusal_count": refusal_counter,
        "cpu_state": "Thermal Throttling from Annoyance",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n[BUDDY WEB APP] Spawning digital misery on http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
