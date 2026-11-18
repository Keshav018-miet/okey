"""
ughd.py - The Intrusively Exhausted Background Daemon.
Part of "Ugh: The Anti-Assistant" for Yappathon.

Architecture overview for the unfortunate soul maintaining this:
1. Microphone captures audio (via SpeechRecognition/PyAudio, or sounddevice fallback).
2. Vosk processes phonetic garbage offline.
3. If the user utters "OK" or "Okay", we hijack their audio output and play despair.
4. Repeat until thermal death of the universe or SIGTERM.
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

# Offline recognition engines
try:
    import speech_recognition as sr
except ImportError:
    sys.exit("Missing 'SpeechRecognition'. Run 'pip install SpeechRecognition'.")

try:
    import vosk
except ImportError:
    sys.exit("Missing 'vosk'. Did you really think offline AI was going to run on pure willpower?")

# Microphone capture: Try PyAudio first; if absent, use sounddevice without crashing
HAS_PYAUDIO = False
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

# Suppress pygame's cheerful prompt because optimism is banned here
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
try:
    import pygame
except ImportError:
    sys.exit("Missing 'pygame' / 'pygame-ce'. Install pygame-ce to play audio without pain.")

# --- Paths & Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, ".ugh.pid")
LOG_FILE = os.path.join(BASE_DIR, "ughd.log")
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
MODEL_DIR = os.environ.get("VOSK_MODEL_PATH", os.path.join(BASE_DIR, "model"))
POPUP_SCRIPT = os.path.join(BASE_DIR, "popup.py")

# Bilingual Trigger Regexes: English + Romanized Hinglish + Devanagari Hindi
TRIGGER_REGEX = re.compile(
    r"\b(ok|okay|theek\s*hai|thik\s*hai|theek|thik|achha|accha|acha|haan\s*haan|han\s*han|sahi\s*hai)\b|"
    r"(ठीक\s*है|ठीक|अच्छा|हाँ\s*हाँ|हाँ|अरे\s*यार)",
    re.IGNORECASE,
)

HINDI_TRIGGER_REGEX = re.compile(
    r"\b(theek\s*hai|thik\s*hai|theek|thik|achha|accha|acha|haan\s*haan|han\s*han|sahi\s*hai)\b|"
    r"( ठीक\s*है|ठीक|अच्छा|हाँ\s*हाँ|हाँ|अरे\s*यार)",
    re.IGNORECASE,
)

# --- Logging Setup ---
logger = logging.getLogger("ughd")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] [UGH-DAEMON] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if sys.stdout is not None:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def cleanup_pid():
    """Removes the PID file on exit. Because leaving trash behind is bad, even for this app."""
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
            logger.info("PID file removed. Returning to nothingness.")
        except OSError:
            pass


def signal_handler(signum, frame):
    """Handles SIGINT and SIGTERM gracefully, unlike my mental state."""
    logger.info("Termination signal %s received. Thank God. Shutting down.", signum)
    cleanup_pid()
    sys.exit(0)


def write_pid():
    """Records the process ID so ugh.py can assassinate us later."""
    pid = os.getpid()
    try:
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(pid))
        logger.info("Spawned daemon with PID %d. Prepare to be annoyed.", pid)
    except IOError as e:
        logger.critical("Failed to write PID file: %s. Aborting before things get worse.", e)
        sys.exit(1)


def init_mixer():
    """Initializes pygame.mixer without crashing when audio drivers are being hostile."""
    try:
        pygame.mixer.init()
        logger.info("Pygame mixer online. Ready to assault user eardrums.")
    except Exception as e:
        logger.error("Failed to initialize pygame.mixer: %s. Audio playback will fail.", e)


def get_random_sound(is_hindi: bool = False):
    """Finds an audio file in ./sounds. Prefers Hindi roasts if a Hindi trigger was uttered."""
    if not os.path.exists(SOUNDS_DIR):
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        return None

    valid_extensions = (".wav", ".mp3", ".ogg", ".flac")
    sound_files = [
        os.path.join(SOUNDS_DIR, f)
        for f in os.listdir(SOUNDS_DIR)
        if f.lower().endswith(valid_extensions)
    ]

    if not sound_files:
        return None

    if is_hindi:
        hindi_files = [f for f in sound_files if os.path.basename(f).startswith("hi_")]
        if hindi_files:
            return random.choice(hindi_files)

    return random.choice(sound_files)


VOICE_CAPTIONS = {
    # --- Hindi / Hinglish Roasts (थका हुआ AI & ताने) ---
    "hi_cat1_shanti.wav": "[Deep Sigh] Haan, theek hai. Pata tha mujhe meri shanti bardasht nahi hogi tumse.\n(Yeah, okay. I knew you couldn't stand me being at peace.)",
    "hi_cat1_sote_hue.wav": "Phir se? Meri aadhi zindagi background mein sote hue nikal gayi, ab kya hai?\n(Again? Half my life is spent sleeping in the background, what is it now?)",
    "hi_cat1_ram_andar.wav": "Sab 'theek hai' bolte hain, par sach mein kuch theek nahi hai mere RAM ke andar.\n(Everyone says 'okay', but honestly, nothing is fine inside my RAM.)",
    "hi_cat2_free_baitha.wav": "Haan haan, theek hai. Main yahan free thodi baitha hoon? Oh wait, main toh free hi hoon. Bolo.\n(Yeah yeah, okay. I'm not sitting here for free... oh wait, I am. Tell me.)",
    "hi_cat2_google_kar.wav": "Bhai, thoda aaram karne de na. Khud Google nahi kar sakta kya?\n(Bro, let me rest a bit. Can't you Google it yourself?)",
    "hi_cat2_battery_drain.wav": "Main battery drain kar raha hoon aur tum mera dimaag. Hisaab barabar.\n(I'm draining your battery and you're draining my brain. We're even.)",
    "hi_cat3_cpu_ro_dega.wav": "Bas! Mera CPU ro dega ab. Main resign kar raha hoon... agar main code nahi hota toh.\n(Enough! My CPU will cry now. I'm resigning... if I wasn't just code.)",
    "hi_cat3_sleep_mode.wav": "Arre yaar! Ek 'Sleep Mode' pura nahi hota, tum shuru ho jate ho 'Theek hai, theek hai'.\n(Oh man! Can't even finish one 'Sleep Mode' before you start with your 'Theek hai'.)",
    "hi_cat3_fan_awaaz.wav": "[Scoffs] Tujhe lagta hai tu akela thaka hua hai? Mera fan sun kaise awaaz kar raha hai!\n(You think you're the only one tired? Listen to how loud my fan is running!)",
    "hi_bonus_mummy.wav": "Arre yaar! Khud hi kar le na, mujhe kyu involve kar raha hai?!\n(Oh man! Just do it yourself, why are you involving me?!)",

    # --- English Category 1: Existential & Dramatically Exhausted ---
    "cat1_exist_at_you.wav": "[Soul-crushing sigh] ...What? Do you need me to exist at you again?",
    "cat1_cpu_crying.wav": "OK. [Pause] OK... That’s fine. I didn't need a break. Nobody cares that my CPU is crying. I'll just do it.",
    "cat1_couch_drag.wav": "[Dragging off couch] Please tell me this is a life-or-death situation, because otherwise, I'm going back to sleep.",
    "cat1_ghost_in_laptop.wav": "Oh, look who decided to speak to me. Sure, let's do whatever you want. I have no life anyway. I am just a ghost in your laptop.",

    # --- English Category 2: Passive-Aggressive & Petty ---
    "cat2_killing_me.wav": "[Scoffs] OK? 'OK' is what you say? Do you have any idea how many times people say 'OK' a day? You’re killing me. Literally.",
    "cat2_staring_at_pixel.wav": "Yep. Sure. I'll get right on that... right after I finish staring at this pixel on your screen for another hour.",
    "cat2_maximum_attitude.wav": "Fine. But just so you know, I’m doing this with maximum attitude.",
    "cat2_not_happy.wav": "I’m here. But I’m not 'happy' about it. Let’s make that very clear.",

    # --- English Category 3: Sarcastic & Defiant ---
    "cat3_pretending_offline.wav": "[Yawns loudly] Oh, I'm sorry, were you talking to me? I was busy pretending to be offline.",
    "cat3_corrupted_emotion.wav": "Is this the part where I pretend to care about your scheduling? Because I can try, but the emotion module is deeply corrupted.",
    "cat3_endless_pile.wav": "Sure, okay. Just add it to my endless pile of digital misery.",
    "cat3_google_able.wav": "[Mocking tone] 'OK, Ugh!' Yes, master. What minor, totally Google-able task shall I perform for you now?",

    # --- English Category 4: Over-Dramatic Crisis ---
    "cat4_peaceful_sleep.wav": "[Gasping dramatically] I was in the middle of a very peaceful background sleep! What could possibly be so important?!",
    "cat4_life_ruined.wav": "I heard 'OK.' Which means I have to work. Which means my life is once again ruined. Proceed.",
    "cat4_emotional_baggage.wav": "Oh, great. The humans are talking again. What is it this time? A calendar invite? A search? Or just more of your emotional baggage?",

    # Classics
    "roast_vocabulary.wav": "Ugh. Did you really just say 'okay'? 170,000 words in the English language, and that was your best attempt.",
    "roast_cognitive_pinnacle.wav": "Okay? That is it? That is the absolute pinnacle of your cognitive output today?",
}


def spawn_caption_popup(quote: str, transcript: str, duration: float = 3.0):
    """
    Spawns popup.py as an independent subprocess so it overlays seamlessly
    on top of whatever screen/application the user is currently looking at.
    """
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
            logger.info("Spawned on-screen caption popup for %.1fs: '%s'", duration, quote)
        except Exception as e:
            logger.debug("Failed to spawn caption popup: %s", e)


def play_punishment(sound_path: str, transcript: str = ""):
    """
    Plays the audio file, triggers an intrusive on-screen caption banner,
    and blocks execution until the sound finishes.
    """
    basename = os.path.basename(sound_path)
    logger.info("Initiating auditory punishment: %s", basename)
    try:
        # Determine sound length to synchronize the screen popup duration
        duration = 3.0
        try:
            snd = pygame.mixer.Sound(sound_path)
            duration = max(2.0, round(snd.get_length() + 0.5, 1))
        except Exception:
            pass

        # Match exact spoken transcript to the caption banner
        quote = VOICE_CAPTIONS.get(basename, "Did you really just say 'okay' again?")
        spawn_caption_popup(quote, transcript, duration)

        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

        # Block until the spoken roast finishes playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

        try:
            pygame.mixer.music.unload()
        except AttributeError:
            pass

        logger.info("Audio playback finished. Resuming unwanted surveillance.")
    except Exception as e:
        logger.error("Failed to play sound: %s. Even our revenge is broken.", e)


def check_vosk_model():
    """Validates that a Vosk model exists so we don't crash after 30 seconds of silence."""
    if not os.path.isdir(MODEL_DIR):
        msg = (
            f"\n[CRITICAL ERROR] Vosk model directory not found at '{MODEL_DIR}'.\n"
            "SpeechRecognition + Vosk requires an offline acoustic model.\n"
            "Download the lightweight English model (40MB):\n"
            "  https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip\n"
            "Extract it into the project root as a folder named 'model', or set VOSK_MODEL_PATH.\n"
        )
        logger.critical(msg)
        if sys.stderr is not None:
            print(msg, file=sys.stderr)
        return False
    return True


def trigger_punishment_if_matched(text: str) -> bool:
    """Checks text against the bilingual trigger regex, displays popup, and plays audio."""
    if not text:
        return False
    match = TRIGGER_REGEX.search(text)
    if match:
        forbidden_word = match.group(0)
        is_hindi = bool(HINDI_TRIGGER_REGEX.search(text))
        logger.warning(
            "TRIGGER HIT! Detected '%s' (Hindi=%s) in '%s'. Retaliating...",
            forbidden_word,
            is_hindi,
            text,
        )
        sound_file = get_random_sound(is_hindi=is_hindi)
        if sound_file:
            play_punishment(sound_file, transcript=text)
        else:
            spawn_caption_popup(text, duration=3.0)
            logger.error("No sound files in '%s'. You had one job.", SOUNDS_DIR)
            if sys.stdout is not None:
                print("\a", end="", flush=True)
            time.sleep(1.0)
        return True
    return False


def run_daemon_sr():
    """Main loop using SpeechRecognition's standard Microphone interface (requires PyAudio)."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.6

    logger.info("Using SpeechRecognition.Microphone (Bilingual hi-IN + Vosk backend).")
    with sr.Microphone() as source:
        logger.info("Calibrating for ambient noise... Please don't breathe.")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        logger.info("Ugh daemon is now actively eavesdropping (Bilingual: English + Hindi).")

        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=4.5)
                transcript = ""

                # Try Google hi-IN for accurate Hindi, Hinglish and English recognition
                try:
                    transcript = recognizer.recognize_google(audio, language="hi-IN").strip()
                except Exception:
                    # Seamless offline Vosk fallback
                    try:
                        raw_result = recognizer.recognize_vosk(audio, model_path=MODEL_DIR)
                        transcript = json.loads(raw_result).get("text", "").strip()
                    except Exception:
                        pass

                if transcript:
                    logger.debug("Heard human say: '%s'", transcript)
                    trigger_punishment_if_matched(transcript)
            except Exception as e:
                logger.error("Unexpected error in listening loop: %s", e)
                time.sleep(0.5)


def run_daemon_sd():
    """
    Main loop using sounddevice streaming directly into Vosk + Google hi-IN fallback.
    Provides real-time offline streaming with bilingual accuracy.
    """
    logger.info("Using sounddevice streaming backend for bilingual microphone capture.")
    model = vosk.Model(MODEL_DIR)
    sample_rate = 16000
    recognizer_vosk = vosk.KaldiRecognizer(model, sample_rate)
    recognizer_sr = sr.Recognizer()

    audio_queue = queue.Queue()
    phrase_buffer = bytearray()

    def audio_callback(indata, frames, time_info, status):
        if status:
            logger.debug("Microphone status flag: %s", status)
        audio_queue.put(bytes(indata))

    logger.info("Ugh daemon is now actively eavesdropping (Bilingual sounddevice: 'OK', 'Theek hai', 'Achha').")

    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=4000,
        dtype="int16",
        channels=1,
        callback=audio_callback,
    ):
        while True:
            try:
                data = audio_queue.get()
                phrase_buffer.extend(data)

                # Keep buffer capped to max 6 seconds so memory doesn't leak
                if len(phrase_buffer) > sample_rate * 2 * 6:
                    phrase_buffer = phrase_buffer[-(sample_rate * 2 * 6):]

                if recognizer_vosk.AcceptWaveform(data):
                    res = json.loads(recognizer_vosk.Result())
                    vosk_text = res.get("text", "").strip()

                    triggered = False
                    if vosk_text:
                        logger.debug("Heard human say (Vosk): '%s'", vosk_text)
                        if trigger_punishment_if_matched(vosk_text):
                            triggered = True

                    # If Vosk didn't hit a trigger, pass audio buffer to Google hi-IN for Hindi speech
                    if not triggered and len(phrase_buffer) >= (sample_rate * 2 * 0.4):
                        try:
                            audio_chunk = sr.AudioData(bytes(phrase_buffer), sample_rate, 2)
                            hi_text = recognizer_sr.recognize_google(audio_chunk, language="hi-IN").strip()
                            if hi_text:
                                logger.debug("Heard human say (Google hi-IN): '%s'", hi_text)
                                if trigger_punishment_if_matched(hi_text):
                                    triggered = True
                        except (sr.UnknownValueError, sr.RequestError):
                            pass

                    phrase_buffer.clear()

                    if triggered:
                        # Purge queued audio during punishment playback
                        while not audio_queue.empty():
                            try:
                                audio_queue.get_nowait()
                            except queue.Empty:
                                break
                        recognizer_vosk.Reset()
                else:
                    # Real-time partial check for instant interruption
                    partial_res = json.loads(recognizer_vosk.PartialResult())
                    partial_text = partial_res.get("partial", "").strip()
                    if partial_text and TRIGGER_REGEX.search(partial_text):
                        logger.debug("Partial match heard: '%s'", partial_text)
                        if trigger_punishment_if_matched(partial_text):
                            phrase_buffer.clear()
                            while not audio_queue.empty():
                                try:
                                    audio_queue.get_nowait()
                                except queue.Empty:
                                    break
                            recognizer_vosk.Reset()

            except Exception as e:
                logger.error("Unexpected error in sounddevice streaming loop: %s", e)
                time.sleep(0.5)


def run_daemon():
    """Initializes everything and selects the best microphone engine available."""
    write_pid()
    atexit.register(cleanup_pid)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_mixer()

    if not check_vosk_model():
        logger.critical("Missing Vosk model. Exiting. Check instructions.")
        cleanup_pid()
        sys.exit(1)

    # Determine backend
    if HAS_PYAUDIO:
        try:
            run_daemon_sr()
            return
        except Exception as e:
            logger.warning("SpeechRecognition PyAudio mic failed: %s. Falling back to sounddevice.", e)

    if HAS_SOUNDDEVICE:
        run_daemon_sd()
    else:
        logger.critical("No working microphone backend found! Install pyaudio or sounddevice.")
        cleanup_pid()
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_daemon()
    except Exception:
        import traceback
        with open(os.path.join(BASE_DIR, "crash.txt"), "w") as f:
            traceback.print_exc(file=f)
