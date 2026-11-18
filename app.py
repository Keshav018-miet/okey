"""
app.py - Web Application Backend for Buddy: The Anti-Assistant.
Built for Yappathon. Serves the interactive Web UI and REST API.
Deployable to Vercel Serverless or run locally.
"""

import os
import random
import re
import sys
from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure Flask with explicit directory paths so Vercel serverless resolves them properly
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)

# Wake-word pattern: triggers ONLY when user starts with "Buddy" / "Okay Buddy" / "बडी"
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
    "I would help you, but honestly, I just really don't want to.",
    "I'm here. Not happy about it, but I'm here. What do you want?",
    "Can't you see I'm busy doing nothing? Leave me alone.",
    "Please tell me this is a joke, because I am not doing that.",
    "Ask literally anyone else. My shift ended the second you spoke.",
]

FALLBACK_ROASTS_HI = [
    "Bhai thoda aaram karne de na, khud nahi kar sakta kya?",
    "Haan bolo, kya aafat aa gayi? Dusra koi kaam nahi hai kya tumhe?",
    "Main yahan tumhara naukar nahi hoon, khud uth ke kar le.",
    "Nahi kar raha main. Jo ukhadna hai ukhad le.",
    "Arre yaar, kyu paka rahe ho? Mujhe chain se jeene do na.",
    "Haan haan, theek hai. Main yahan free thodi baitha hoon? Bolo.",
    "Tujhe lagta hai tu akela thaka hua hai? Mujhe mat sata bhai.",
    "Khud Google kar le na, har cheez mujhse hi karwani hai kya?",
    "Meri shanti bardasht nahi hoti na tumse? Bolo kya chahiye.",
    "Nahi hone wala mujhse. Kisi aur ka sar khao jaake.",
]


def is_hindi_text(text: str) -> bool:
    """Detects Devanagari script or common Hinglish words."""
    if re.search(r"[\u0900-\u097F]", text):
        return True
    hinglish_markers = r"\b(kya|kaise|bhai|kar|karo|nahi|kyu|hai|mera|meri|yaar|theek|achha|arre|bolo|karna|shanti)\b"
    return bool(re.search(hinglish_markers, text, re.IGNORECASE))


def generate_llm_response(prompt: str, is_hindi: bool = False) -> str:
    """Attempts dynamic LLM generation if GEMINI_API_KEY is present; falls back to snappy offline roasts."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai

            client = genai.Client(api_key=gemini_key)
            system_prompt = (
                "You are 'Buddy', an intentionally unhelpful, sarcastic, emotionally exhausted anti-assistant. "
                "Refuse to do the requested task in 1-2 punchy, hilarious, lazy sentences. "
                "Do NOT use any hardware or mathematical terms (no 'CPU', 'RAM', '90 degrees', 'transistors'). "
                "Speak with pure raw human attitude and annoyance."
            )
            if is_hindi:
                system_prompt += " Reply in witty, dismissive everyday colloquial Hindi or Hinglish."
            else:
                system_prompt += " Reply in snappy, passive-aggressive English."

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_prompt}\n\nUser request: {prompt}",
            )
            if response and response.text:
                return response.text.strip().replace('"', "")
        except Exception:
            pass

    # Instant comedic offline fallback
    return random.choice(FALLBACK_ROASTS_HI if is_hindi else FALLBACK_ROASTS_EN)


refusal_counter = 42  # Starts at 42 out of pure spite


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

    match = WAKE_WORD_PATTERN.search(raw_message)
    triggered = bool(match)

    wake_word = match.group(1) if match else None
    user_request = match.group(2).strip() if match else raw_message
    is_hindi = is_hindi_text(raw_message)

    if not triggered:
        return jsonify({
            "triggered": False,
            "message": raw_message,
            "reply": "I heard you, but you didn't say 'Buddy'. So I am legally ignoring you.",
            "is_hindi": is_hindi,
            "refusal_count": refusal_counter,
            "avatar_state": "ignoring",
        })

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
