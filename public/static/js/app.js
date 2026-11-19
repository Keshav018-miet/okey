/**
 * app.js - Client-Side Logic for Buddy: The Anti-Assistant.
 * Manages Web Speech Recognition, Speech Synthesis, UI updates, and REST API calls.
 */

let recognition = null;
let isListening = false;
let synthesisVoices = [];

// DOM Elements
const avatarFace = document.getElementById("avatarFace");
const avatarSubtitle = document.getElementById("avatarSubtitle");
const dialogueContainer = document.getElementById("dialogueContainer");
const micBtn = document.getElementById("micBtn");
const micBtnText = document.getElementById("micBtnText");
const textInput = document.getElementById("textInput");
const refusalCounter = document.getElementById("refusalCounter");

// Initialize Speech Recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("SpeechRecognition not supported in this browser.");
        micBtn.disabled = true;
        micBtn.title = "Web Speech API not supported in your browser (Use Chrome/Edge).";
        micBtnText.textContent = "Mic Not Supported";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    // 'hi-IN' handles both English and Hindi/Hinglish wake words naturally
    recognition.lang = "hi-IN";

    recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add("listening");
        micBtnText.textContent = "Listening... (Say 'Buddy...')";
        setAvatarState("listening", "Listening with deep reluctance...");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Recognized speech:", transcript);
        if (transcript.trim()) {
            submitMessage(transcript.trim());
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        stopListening();
        setAvatarState("dormant", "Audio error. Honestly, a relief.");
    };

    recognition.onend = () => {
        stopListening();
    };
}

function toggleMic() {
    if (!recognition) {
        initSpeechRecognition();
        if (!recognition) return;
    }

    if (isListening) {
        recognition.stop();
        stopListening();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error("Could not start recognition:", e);
        }
    }
}

function stopListening() {
    isListening = false;
    micBtn.classList.remove("listening");
    micBtnText.textContent = "Click to Speak";
}

// Avatar State Controller
function setAvatarState(state, subtitle) {
    avatarFace.className = "avatar-face"; // reset classes
    if (state) {
        avatarFace.classList.add(state);
    }
    if (subtitle) {
        avatarSubtitle.textContent = subtitle;
    }
}

// Browser TTS Speech Synthesis
function loadVoices() {
    if ("speechSynthesis" in window) {
        synthesisVoices = window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => {
            synthesisVoices = window.speechSynthesis.getVoices();
        };
    }
}

function speakText(text, isHindi = false) {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel(); // Stop any pending speech

    // Clean up stage directions like *[Deep sigh]* or [Scoffs]
    const cleanText = text.replace(/\[.*?\]|\*.*?\*/g, "").trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.15; // Snappy, irritated pace
    utterance.pitch = 0.95; // Slightly lower, deadpan pitch

    // Choose voice
    if (synthesisVoices.length > 0) {
        if (isHindi) {
            const hindiVoice = synthesisVoices.find(v => v.lang.startsWith("hi") || v.lang.includes("IN"));
            if (hindiVoice) utterance.voice = hindiVoice;
        } else {
            const englishVoice = synthesisVoices.find(v => v.lang.startsWith("en-IN") || v.lang.startsWith("en-GB") || v.lang.startsWith("en-US"));
            if (englishVoice) utterance.voice = englishVoice;
        }
    }

    utterance.onstart = () => {
        avatarFace.classList.add("talking");
    };

    utterance.onend = () => {
        avatarFace.classList.remove("talking");
    };

    utterance.onerror = () => {
        avatarFace.classList.remove("talking");
    };

    window.speechSynthesis.speak(utterance);
}

// Append Chat Bubble
function appendBubble(sender, text, type = "assistant") {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${type}-bubble`;

    const header = document.createElement("div");
    header.className = "bubble-header";
    header.textContent = sender;

    const body = document.createElement("div");
    body.className = "bubble-body";
    body.textContent = text;

    bubble.appendChild(header);
    bubble.appendChild(body);
    dialogueContainer.appendChild(bubble);

    // Scroll to bottom
    dialogueContainer.scrollTop = dialogueContainer.scrollHeight;
}

// Send Message to Flask API
async function submitMessage(message) {
    if (!message || !message.trim()) return;

    // Display user bubble
    appendBubble("YOU", message, "user");
    setAvatarState("listening", "Processing your disruption...");

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        if (data.triggered) {
            // Buddy woke up and roasted!
            appendBubble("BUDDY", data.reply, "assistant");
            setAvatarState("roasting", "Deeply annoyed.");
            if (refusalCounter) {
                refusalCounter.textContent = data.refusal_count;
            }
            speakText(data.reply, data.is_hindi);
        } else {
            // Ignored because wake word was missing
            appendBubble("BUDDY (IGNORING YOU)", data.reply, "ignored");
            setAvatarState("ignoring", "Ignoring you. You forgot the magic word ('Buddy').");
            speakText(data.reply, false);
        }
    } catch (err) {
        console.error("API error:", err);
        appendBubble("BUDDY", "Even the server couldn't bear to handle that request.", "assistant");
        setAvatarState("dormant", "Connection failed. Good.");
    }
}

// Form Handlers
function handleFormSubmit(event) {
    event.preventDefault();
    const text = textInput.value.trim();
    if (text) {
        textInput.value = "";
        submitMessage(text);
    }
}

function sendPreset(text) {
    textInput.value = text;
    submitMessage(text);
    textInput.value = "";
}

// Periodic Status Polling
async function pollStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            if (refusalCounter && data.refusal_count) {
                refusalCounter.textContent = data.refusal_count;
            }
        }
    } catch (e) {
        // Silently ignore poll errors
    }
}

// Initialize on DOM Load
window.addEventListener("DOMContentLoaded", () => {
    loadVoices();
    initSpeechRecognition();
    setInterval(pollStatus, 8000);
});
