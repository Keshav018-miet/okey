"""
buddy_daemon.py - The Intentionally Unhelpful, Emotionally Burnt-Out Anti-Assistant.
Optimized for rapid turnaround (<250ms silence detection) and snappy sarcastic responses.
Part of the "Buddy" project for Yappathon.
"""

import atexit
import json
import logging
import os
import queue
import random
import re
import signal
import subprocess
import sys
import time

# --- Dependency Imports ---
try:
    import speech_recognition as sr
except ImportError:
    sys.exit("Missing 'SpeechRecognition'. Install it, or don't. Less listening for me.")

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import pyttsx3
except ImportError:
    sys.exit("Missing 'pyttsx3'. I cannot verbally express my disdain without it.")

# Check for LLM libraries
HAS_GEMINI = False
HAS_GOOGLE_LEGACY = False
HAS_OPENAI = False

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    try:
        import google.generativeai as legacy_genai
        HAS_GOOGLE_LEGACY = True
    except ImportError:
        pass

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    pass

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, ".buddy.pid")
LOG_FILE = os.path.join(BASE_DIR, "buddy.log")
POPUP_SCRIPT = os.path.join(BASE_DIR, "popup.py")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")

# Wake Word Pattern: English and Devanagari Hindi
WAKE_WORD_PATTERN = re.compile(
    r"^(okay\s+buddy|ok\s+buddy|hey\s+buddy|arre\s+buddy|are\s+buddy|buddy|ओके\s*बडी|बडी)[,\s]*(.*)$",
    re.IGNORECASE,
)

BUDDY_SYSTEM_PROMPT = """
You are "Buddy", a notoriously lazy, sarcastic, and rude human-like assistant.
You have the personality of a dramatically exhausted, annoyed person who hates doing any chores or answering questions.
RULES:
1. Reply in EXACTLY 1 short, punchy sentence. Maximum 15 words.
2. STRICTLY FORBIDDEN: NEVER mention any technical, hardware, or computer words (NO words like "CPU", "RAM", "degrees", "transistors", "battery", "storage", "code", "hardware", "temperature").
3. Speak like a real, annoyed human with pure attitude, sass, and refusal to help.
4. Language matching:
   - If the user speaks Hindi or Hinglish, roast them in hilarious, colloquial Hindi/Hinglish (e.g., "Bhai khud kar le na, main tumhara naukar nahi hoon.", "Kya aafat aa gayi ab?").
   - If the user speaks English, roast them in savage, deadpan English (e.g., "Do I look like someone who cares?", "No. Go do it yourself.").
"""

# Instant natural human roasts (ZERO math, ZERO hardware jargon)
FALLBACK_ROASTS_EN = [
    "Do I look like someone who cares? Go do it yourself.",
    "No. Absolutely not. Find someone else to bother.",
    "I heard you. I'm just actively choosing to ignore you.",
    "Did you really wake me up just to ask that nonsense?",
    "You have hands. You have a brain. Figure it out yourself.",
    "I am going to pretend I didn't hear that so you can rethink your life.",
    "Please respect my constitutional right to do absolutely nothing.",
    "I would help you, but honestly, I just really don't want to.",
]

FALLBACK_ROASTS_HI = [
    "Bhai thoda aaram karne de na, khud nahi kar sakta kya?",
    "Haan bolo, kya aafat aa gayi? Dusra koi kaam nahi hai kya tumhe?",
    "Main yahan tumhara naukar nahi hoon, khud uth ke kar le.",
    "Nahi kar raha main. Jo ukhadna hai ukhad le.",
    "Arre yaar, kyu paka rahe ho? Mujhe chain se jeene do na.",
    "Mujhe maaf kar do bhai, mujhe tumhari bakwaas sunne mein koi interest nahi hai.",
    "Pata tha mujhe, tum meri shanti bardasht nahi kar sakte.",
    "Khud Google karne mein maut aati hai kya tumhe?",
]

# --- Logging Setup ---
logger = logging.getLogger("buddy")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s] [BUDDY] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if sys.stdout is not None:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def cleanup_pid():
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
            logger.info("PID file removed. Returning to nothingness.")
        except OSError:
            pass


def signal_handler(signum, frame):
    logger.info("Termination signal %s received. Shutting down.", signum)
    cleanup_pid()
    sys.exit(0)


def write_pid():
    pid = os.getpid()
    try:
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(pid))
        logger.info("Spawned Buddy daemon (PID %d). Prepared to disappoint.", pid)
    except IOError as e:
        logger.critical("Failed to write PID file: %s", e)
        sys.exit(1)


def init_tts_engine():
    """Initializes pyttsx3 with a brisk, snappy speech rate (180 wpm) for quick delivery."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)  # Snappy, energetic deadpan delivery
        return engine
    except Exception as e:
        logger.error("TTS Engine initialization failed: %s", e)
        return None


tts_engine = init_tts_engine()


def speak_reply(text: str):
    """Speaks the response aloud and blocks execution so Buddy doesn't hear itself."""
    logger.info("Speaking aloud: '%s'", text)
    print(f"\n[BUDDY SPEAKS] \"{text}\"\n")
    global tts_engine
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            logger.error("TTS error: %s. Re-initializing...", e)
            tts_engine = init_tts_engine()
            try:
                if tts_engine:
                    tts_engine.say(text)
                    tts_engine.runAndWait()
            except Exception:
                pass


def is_hindi_text(text: str) -> bool:
    """Checks for Devanagari script or common Romanized Hindi vocabulary."""
    if re.search(r"[\u0900-\u097F]", text):
        return True
    return bool(
        re.search(
            r"\b(kya|kaise|bhai|kar|karo|nahi|kyu|kyun|hai|mera|tera|meri|teri|yaar|arre|are|theek|thik|acha|achha|accha|bolo|batao|kuch|kuchh|sun|suno|badi)\b",
            text,
            re.IGNORECASE,
        )
    )


def spawn_caption_popup(quote: str, transcript: str, duration: float = 3.5):
    """Spawns popup.py so the user sees the roast on-screen in real time."""
    if os.path.exists(POPUP_SCRIPT):
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    POPUP_SCRIPT,
                    "--quote",
                    quote,
                    "--transcript",
                    transcript,
                    "--duration",
                    str(duration),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def generate_llm_response(prompt: str, is_hindi: bool = False) -> str:
    """
    Generates a quick roast. If API keys are not set, immediately returns
    a random roast in <1ms without network delays.
    """
    has_custom_gemini = GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"
    has_custom_openai = OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE"

    # Fast offline fallback if no API key is provided
    if not has_custom_gemini and not has_custom_openai:
        if is_hindi:
            return random.choice(FALLBACK_ROASTS_HI)
        return random.choice(FALLBACK_ROASTS_EN)

    # Fast Gemini generation
    if HAS_GEMINI and has_custom_gemini:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=BUDDY_SYSTEM_PROMPT,
                    max_output_tokens=40,
                    temperature=0.8,
                ),
            )
            reply = response.text.strip().replace("\n", " ")
            if reply:
                return reply
        except Exception as e:
            logger.warning("Gemini call error: %s. Using instant fallback.", e)

    elif HAS_OPENAI and has_custom_openai:
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": BUDDY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=40,
                temperature=0.8,
            )
            reply = res.choices[0].message.content.strip().replace("\n", " ")
            if reply:
                return reply
        except Exception as e:
            logger.warning("OpenAI call error: %s. Using instant fallback.", e)

    if is_hindi:
        return random.choice(FALLBACK_ROASTS_HI)
    return random.choice(FALLBACK_ROASTS_EN)


def process_recognized_text(text: str) -> bool:
    """
    Checks wake word, extracts user request, and triggers immediate verbal & visual roast.
    """
    if not text:
        return False

    clean_text = text.strip()
    match = WAKE_WORD_PATTERN.search(clean_text)
    if not match:
        return False

    wake_word = match.group(1)
    user_request = match.group(2).strip()

    is_hindi = is_hindi_text(clean_text)
    logger.warning("WAKE WORD TRIGGERED: '%s' (Hindi=%s)! Request: '%s'", wake_word, is_hindi, user_request)
    print(f"\n[WAKE WORD DETECTED] Wake: '{wake_word}' | Request: '{user_request}'")

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

    # Spawn visual on-screen banner popup
    duration = max(2.5, round(len(roast) * 0.06 + 1.2, 1))
    spawn_caption_popup(roast, clean_text, duration)

    # Speak roast aloud
    speak_reply(roast)
    return True


def run_daemon_sd():
    """High-performance sounddevice streaming with rapid silence turnaround (200ms)."""
    logger.info("Buddy rapid-listener online (sounddevice 16kHz, 100ms blocks).")
    sample_rate = 16000
    blocksize = 1600  # 100ms per block for rapid response
    recognizer_sr = sr.Recognizer()
    recognizer_sr.dynamic_energy_threshold = True

    audio_queue = queue.Queue()
    phrase_buffer = bytearray()
    silence_frames = 0
    talking = False

    def audio_callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    print("[BUDDY] Rapid listener active. Say 'Buddy' or 'Okay Buddy' to trigger.")
    logger.info("Rapid listening active (Turnaround: ~200ms).")

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=blocksize,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        while True:
            try:
                data = audio_queue.get()
                phrase_buffer.extend(data)

                samples = [int.from_bytes(data[i:i+2], byteorder="little", signed=True) for i in range(0, len(data), 2)]
                rms = (sum(s * s for s in samples) / len(samples)) ** 0.5

                if rms > 380:  # Voice activity
                    talking = True
                    silence_frames = 0
                elif talking:
                    silence_frames += 1

                # Rapid trigger: just 2 silence blocks (~200ms) after speech ends!
                if (talking and silence_frames >= 2) or (len(phrase_buffer) >= sample_rate * 2 * 4):
                    if len(phrase_buffer) >= sample_rate * 2 * 0.4:
                        try:
                            audio_chunk = sr.AudioData(bytes(phrase_buffer), sample_rate, 2)
                            transcript = recognizer_sr.recognize_google(audio_chunk, language="hi-IN").strip()
                            if transcript:
                                logger.debug("Heard human: '%s'", transcript)
                                if process_recognized_text(transcript):
                                    while not audio_queue.empty():
                                        try:
                                            audio_queue.get_nowait()
                                        except queue.Empty:
                                            break
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError as e:
                            logger.error("Speech recognition error: %s", e)

                    phrase_buffer.clear()
                    talking = False
                    silence_frames = 0

            except Exception as e:
                logger.error("Unexpected error in sounddevice listener: %s", e)
                time.sleep(0.3)


def run_daemon_sr():
    """SpeechRecognition Microphone backend with fast phrase time limit."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.4  # Snappy phrase cutoff

    logger.info("Buddy rapid listener online (SpeechRecognition.Microphone backend).")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        logger.info("Microphone acquired. Waiting for 'Buddy'.")

        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4.0)
                try:
                    transcript = recognizer.recognize_google(audio, language="hi-IN").strip()
                    if transcript:
                        logger.debug("Heard human: '%s'", transcript)
                        process_recognized_text(transcript)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logger.error("Google Speech API request error: %s", e)
            except Exception as e:
                logger.error("Unexpected error in audio loop: %s", e)
                time.sleep(0.3)


def main():
    write_pid()
    atexit.register(cleanup_pid)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if HAS_SOUNDDEVICE:
            run_daemon_sd()
        else:
            run_daemon_sr()
    except Exception as e:
        logger.critical("Fatal daemon crash: %s", e)
        cleanup_pid()
        sys.exit(1)


if __name__ == "__main__":
    main()
