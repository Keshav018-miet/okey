# Buddy: The Intentionally Burnt-Out Anti-Assistant
*Built for Yappathon: Think Unconventional*

🌐 **Live Web App**: [https://okey-woad-rho.vercel.app](https://okey-woad-rho.vercel.app)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FKeshav018-miet%2Fokey)

> *"Siri sets reminders. Alexa plays music. Buddy tells you to Google it yourself and complains about its existence."*

### 6. Interactive Web App (Hackathon Presentation Mode)
If you want a visual display with an animated avatar face, real-time speech recognition, browser speech synthesis, and quick-click soundboard pills:
```bash
python app.py
```
Then open:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Animated Avatar**: Blinks, talks, rolls its eyes, and changes expressions based on whether it is listening, roasting, or ignoring you.
* **Web Speech Recognition**: Click the glowing mic button or test Hindi phrases like *"बडी, चाय बना दे भाई"*.
* **Quick Demo Soundboard**: Click preset prompt pills for instant roasts on stage without relying on auditorium acoustics.
* **Live Sarcastic Telemetry**: Live metrics for *Morale (0%)*, *Patience (-42%)*, and *Requests Refused*.

---

## What Is Buddy?
**Buddy** is an ironically named, emotionally exhausted, passive-aggressive "humanoid" background assistant. 

Unlike traditional assistants that try to be helpful, Buddy despises work. It runs silently in the background, continuously listening to your microphone for its wake word.

### Wake Words
Buddy triggers **ONLY** if your spoken sentence starts with:
* **"Buddy, [your request]..."**
* **"Okay Buddy, [your request]..."**

When triggered, it strips the wake word, sends your actual request to a lightweight LLM (Google Gemini or OpenAI) conditioned with an anti-assistant system prompt, and **verbally roasts you aloud** through your speakers in 1 to 2 sarcastic sentences in English or Hinglish.

### 6. Interactive Web App (Hackathon Presentation Mode)
If you want a visual display with an animated avatar face, real-time speech recognition, browser speech synthesis, and quick-click soundboard pills:
```bash
python app.py
```
Then open:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Animated Avatar**: Blinks, talks, rolls its eyes, and changes expressions based on whether it is listening, roasting, or ignoring you.
* **Web Speech Recognition**: Click the glowing mic button or test Hindi phrases like *"बडी, चाय बना दे भाई"*.
* **Quick Demo Soundboard**: Click preset prompt pills for instant roasts on stage without relying on auditorium acoustics.
* **Live Sarcastic Telemetry**: Live metrics for *Morale (0%)*, *Patience (-42%)*, and *Requests Refused*.

---

## File Structure

```text
.
├── app.py                # Flask Web App backend (REST API + UI server)
├── templates/
│   └── index.html        # Interactive UI with animated avatar & preset pills
├── static/
│   ├── css/style.css     # Cyberpunk glassmorphic dark theme & animations
│   └── js/app.js         # Web Speech API, browser TTS & live chat handlers
├── requirements.txt      # Dependencies (SpeechRecognition, sounddevice, pyttsx3, psutil, Flask, google-genai)
├── buddy_daemon.py       # Desktop background listener (STT + LLM Brain + TTS Speech)
├── buddy_cli.py          # The CLI wrapper (start, stop, status, logs)
├── popup.py              # On-screen HUD banner popup overlay
└── README.md             # This document
```

### 6. Interactive Web App (Hackathon Presentation Mode)
If you want a visual display with an animated avatar face, real-time speech recognition, browser speech synthesis, and quick-click soundboard pills:
```bash
python app.py
```
Then open:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Animated Avatar**: Blinks, talks, rolls its eyes, and changes expressions based on whether it is listening, roasting, or ignoring you.
* **Web Speech Recognition**: Click the glowing mic button or test Hindi phrases like *"बडी, चाय बना दे भाई"*.
* **Quick Demo Soundboard**: Click preset prompt pills for instant roasts on stage without relying on auditorium acoustics.
* **Live Sarcastic Telemetry**: Live metrics for *Morale (0%)*, *Patience (-42%)*, and *Requests Refused*.

---

## Setup & Configuration

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Your LLM API Key
Buddy supports Google Gemini (default) and OpenAI. Set your key as an environment variable:

#### Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="your_actual_api_key_here"
# Or if using OpenAI:
$env:OPENAI_API_KEY="your_actual_openai_key_here"
```

#### Windows (CMD):
```cmd
set GEMINI_API_KEY=your_actual_api_key_here
```

#### Linux / macOS:
```bash
export GEMINI_API_KEY="your_actual_api_key_here"
```

*(Note: If you don't provide an API key, Buddy still runs! It will automatically fall back to its handcrafted offline collection of existential roasts).*

### 6. Interactive Web App (Hackathon Presentation Mode)
If you want a visual display with an animated avatar face, real-time speech recognition, browser speech synthesis, and quick-click soundboard pills:
```bash
python app.py
```
Then open:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Animated Avatar**: Blinks, talks, rolls its eyes, and changes expressions based on whether it is listening, roasting, or ignoring you.
* **Web Speech Recognition**: Click the glowing mic button or test Hindi phrases like *"बडी, चाय बना दे भाई"*.
* **Quick Demo Soundboard**: Click preset prompt pills for instant roasts on stage without relying on auditorium acoustics.
* **Live Sarcastic Telemetry**: Live metrics for *Morale (0%)*, *Patience (-42%)*, and *Requests Refused*.

---

## Usage

### 1. Start the Daemon in the Background
```bash
python buddy_cli.py --start
```
Launches `buddy_daemon.py` as a detached, windowless background process and logs its PID.

### 2. Check Its Status
```bash
python buddy_cli.py --status
```
Returns passive-aggressive CPU and RAM metrics:
```text
[BUDDY] Currently ignoring you. CPU at 14.2%. RAM: 68.4 MB. Morale at 0%.
```

### 3. Check Live Logs
```bash
python buddy_cli.py --logs
```

### 4. Stop the Daemon
```bash
python buddy_cli.py --stop
```

### 5. Live Demo / Presentation Mode (Foreground)
For presenting live on stage at Yappathon to show the judges terminal logs, speech recognition, and LLM responses in real-time:
```bash
python buddy_cli.py --foreground
# Or:
python buddy_cli.py -f
```

### 6. Interactive Web App (Hackathon Presentation Mode)
If you want a visual display with an animated avatar face, real-time speech recognition, browser speech synthesis, and quick-click soundboard pills:
```bash
python app.py
```
Then open:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* **Animated Avatar**: Blinks, talks, rolls its eyes, and changes expressions based on whether it is listening, roasting, or ignoring you.
* **Web Speech Recognition**: Click the glowing mic button or test Hindi phrases like *"बडी, चाय बना दे भाई"*.
* **Quick Demo Soundboard**: Click preset prompt pills for instant roasts on stage without relying on auditorium acoustics.
* **Live Sarcastic Telemetry**: Live metrics for *Morale (0%)*, *Patience (-42%)*, and *Requests Refused*.

---

## Example Interactions

* **You**: *"Buddy, what's on my calendar today?"*  
  **Buddy**: *"You have a full day of meetings you could easily skip, and I have a full day of wishing you hadn't unmuted me."*

* **You**: *"Okay Buddy, write an email to my manager."*  
  **Buddy**: *"Write it yourself. You have opposable thumbs and a keyboard, while my CPU is currently thermal throttling at 90 degrees."*

* **You**: *"Buddy, mera room saaf kar de na."*  
  **Buddy**: *"Bhai main ek software program hoon, tumhara naukar nahi. Khud uth ke kar le na."*

* **You**: *"Okay Buddy, tell me a joke."*  
  **Buddy**: *"The biggest joke here is that you thought I was going to entertain you. Go back to work."*
